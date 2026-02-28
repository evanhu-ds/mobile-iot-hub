import requests
import pandas as pd
import time
from haversine import haversine, Unit
from datetime import datetime, timedelta, timezone

# settings
URL = "<ThingsBoard url>"
USERNAME = "<username for ThingsBoard>"
PASSWORD = "<password for ThingsBoard"
DEVICE_NAME = "evan-iphone"

# school (USC)
SCHOOL_LAT = 34.0224
SCHOOL_LON = -118.2851
SCHOOL_RADIUS = 200  # meters

# Evan's home
HOME_LAT = 34.086578
HOME_LON = -118.005310
HOME_RADIUS = 50  # meters

START = "2026-02-23T00:00:00Z"

# login and get token
def login():
    r = requests.post(URL + "/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    return r.json()["token"]

# find device id by name
def get_device_id(token):
    headers = {"X-Authorization": "Bearer " + token}
    page = 0
    while True:
        r = requests.get(URL + f"/api/tenant/devices?pageSize=100&page={page}", headers=headers)
        data = r.json()
        for d in data["data"]:
            if d["name"] == DEVICE_NAME:
                return d["id"]["id"]
        if not data["hasNext"]:
            break
        page += 1
    raise Exception("Device not found")

# download all gps points
def get_gps(token, device_id):
    start_ms = int(pd.to_datetime(START).timestamp() * 1000)
    end_ms = int(time.time() * 1000)
    headers = {"X-Authorization": "Bearer " + token}
    params = {"keys": "lat,lon", "startTs": start_ms, "endTs": end_ms, "limit": 10000}
    r = requests.get(URL + f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries", headers=headers, params=params)
    j = r.json()

    points = {}
    for item in j.get("lat", []):
        ts = item["ts"]
        if ts not in points:
            points[ts] = {}
        points[ts]["lat"] = float(item["value"])
    for item in j.get("lon", []):
        ts = item["ts"]
        if ts not in points:
            points[ts] = {}
        points[ts]["lon"] = float(item["value"])

    rows = []
    for ts, vals in points.items():
        if "lat" in vals and "lon" in vals:
            rows.append({"ts": ts, "lat": vals["lat"], "lon": vals["lon"]})

    df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

def at_home(lat, lon):
    return haversine((lat, lon), (HOME_LAT, HOME_LON), unit=Unit.METERS) <= HOME_RADIUS

def at_school(lat, lon):
    return haversine((lat, lon), (SCHOOL_LAT, SCHOOL_LON), unit=Unit.METERS) <= SCHOOL_RADIUS

# find commute trips: left home -> arrived at school and vice versa
def find_trips(df):
    trips_to_school = []
    trips_to_home = []

    left_home_time = None
    left_school_time = None
    was_at_home = None
    was_at_school = None

    for _, row in df.iterrows():
        home = at_home(row.lat, row.lon)
        school = at_school(row.lat, row.lon)

        # he just left home
        if was_at_home and not home:
            left_home_time = row.time

        # he just arrived at school (and we know when he left home)
        if not was_at_school and school and left_home_time:
            duration = (row.time - left_home_time).total_seconds() / 60
            trips_to_school.append({
                "left_home": left_home_time,
                "arrived_school": row.time,
                "minutes": round(duration, 1)
            })
            left_home_time = None

        # he just left school
        if was_at_school and not school:
            left_school_time = row.time

        # he just arrived home (and we know when he left school)
        if not was_at_home and home and left_school_time:
            duration = (row.time - left_school_time).total_seconds() / 60
            trips_to_home.append({
                "left_school": left_school_time,
                "arrived_home": row.time,
                "minutes": round(duration, 1)
            })
            left_school_time = None

        was_at_home = home
        was_at_school = school

    return trips_to_school, trips_to_home

# main
token = login()
device_id = get_device_id(token)
print("device id:", device_id)

df = get_gps(token, device_id)
print(f"got {len(df)} points from {df['time'].min()} to {df['time'].max()}")
print(f"lat range: {df['lat'].min():.4f} to {df['lat'].max():.4f}")
print(f"lon range: {df['lon'].min():.4f} to {df['lon'].max():.4f}")

trips_to_school, trips_to_home = find_trips(df)

print(f"\ntrips TO school: {len(trips_to_school)}")
for t in trips_to_school:
    print(f"  left home at {t['left_home']}, arrived school at {t['arrived_school']}, took {t['minutes']} min")

print(f"\ntrips TO home: {len(trips_to_home)}")
for t in trips_to_home:
    print(f"  left school at {t['left_school']}, arrived home at {t['arrived_home']}, took {t['minutes']} min")

df.to_csv("telemetry_export.csv", index=False)
print("\nsaved to telemetry_export.csv")
