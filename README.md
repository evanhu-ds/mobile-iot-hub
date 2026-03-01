# Mobile IoT Telemetry Platform 

## Overview
In this project, we built an end-to-end IoT pipeline:

Smartphone (OwnTracks) → ThingsBoard (AWS EC2) → Telemetry Storage → Dashboard Visualization → Data Analysis

GPS telemetry is transmitted in real time from a mobile device to a cloud-hosted ThingsBoard instance. The data is visualized through dashboards and further analyzed using a custom Python script.

## Repository Contents
* `device_telemetry.py`

    Python script that:
    * Authenticates with the ThingsBoard REST API
    * Retrieves historical GPS telemetry (latitude/longitude)
    * Applies geofencing logic (home and USC campus locations)
    * Detects commute trips and calculates travel duration
    * Exports processed telemetry data to CSV

* `telemetry_export.csv`
    * Sample output generated from the script containing timestamped GPS telemetry data.

## Key Features
* Real-time GPS streaming from smartphone
* Cloud-based IoT hub deployment (AWS EC2)
* Dashboard map visualization (OpenStreetMap widget)
* Automated commute detection using Haversine distance
* Travel time computation and CSV export

## Technologies Used
* AWS EC2 (Ubuntu)
* ThingsBoard Community Edition
* OwnTracks (mobile telemetry)
* PostgreSQL
* Python (requests, pandas, haversine)

## Purpose
This lab project demonstrates how mobile devices can function as IoT sensors and how cloud infrastructure can be used to ingest, visualize, and analyze telemetry data at scale.
