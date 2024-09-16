from flask import Flask, jsonify, send_from_directory
from skyfield.api import EarthSatellite, load, utc
from datetime import datetime, timezone
from skyfield.api import wgs84
from skyfield.framelib import itrs
import numpy as np
import math
from satellite_tle import fetch_all_tles, fetch_latest_tles

# Taskable: Yellow
# Nontaskable: Green

app = Flask(__name__)

# Load the timescale
ts = load.timescale()

# # Define the satellites
# satellites = [
#     {
#         "name": "CAPELLA-14 (ACADIA-4)",
#         "tle": [
#             "1 59444U 24066C   24255.58733490  .00027683  00000+0  27717-2 0  9992",
#             "2 59444  45.6105 355.6094 0002469 338.3298  21.7475 14.91016875 15732"
#         ]
#     },
#     {
#         "name": "GCOM-W1 (SHIZUKU)",
#         "tle": [
#             "1 38337U 12025A   24256.58148722  .00002449  00000+0  55400-3 0  9995",
#             "2 38337  98.2068 195.3055 0002169 106.7341  66.3204 14.57058865655452"
#         ]
#     },
#     {
#         "name": "NOAA 20 (JPSS-1)",
#         "tle": [
#             "1 43013U 17073A   24260.54824830  .00000349  00000+0  18598-3 0  9996",
#             "2 43013  98.7099 196.9501 0001127  22.2184 337.9041 14.19588559353863"
#         ]
#     }
# ]

# # Load the satellites
# satellite_objects = [
#     EarthSatellite(sat["tle"][0], sat["tle"][1], sat["name"], ts=ts)
#     for sat in satellites
# ]

# Define the NORAD IDs
norad_ids = [59444,  # CAPELLA-14 (ACADIA-4)
             38337,  # GCOM-W1 (SHIZUKU)
             43013]  # NOAA 20 (JPSS-1)

# Fetch the latest TLEs for the satellites
tles = fetch_latest_tles(norad_ids)

# # Create the satellite objects
# satellite_objects = [
#     EarthSatellite(tle[0], tle[1], str(norad_id), ts=ts)
#     for norad_id, tle in tles.items()
# ]
satellite_objects = []

for norad_id, tle in tles.items():
    satellite = EarthSatellite(tle[1][1], tle[1][2], str(tle[1][0]), ts=ts)
    satellite_objects.append(satellite)

def calculate_angular_width(altitude_m):
    altitude_km = altitude_m / 1000
    R = 6371
    theta_radians = 2 * math.atan(R / (R + altitude_km))
    theta_degrees = math.degrees(theta_radians)
    return theta_degrees

def compute_min_elevation(altitude, field_of_regard):
    earth_equatorial_radius = 6378137.000000000
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    sin_eta = np.sin(np.radians(field_of_regard / 2))
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    cos_epsilon = sin_eta / sin_rho
    if cos_epsilon > 1:
        return 0.0
    return np.degrees(np.arccos(cos_epsilon))

def compute_sensor_radius(altitude, min_elevation):
    earth_equatorial_radius = 6378137.0
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
    sw_HalfAngle = 90 - eta - min_elevation
    if sw_HalfAngle < 0.0:
        return 0.0
    return earth_mean_radius * np.radians(sw_HalfAngle)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/get_positions')
def get_positions():
    current_datetime = datetime.now(timezone.utc)
    positions = []

    for satellite in satellite_objects:
        position = satellite.at(ts.from_datetime(current_datetime))
        subpoint = wgs84.subpoint(position)
        lat, lon = subpoint.latitude, subpoint.longitude
        altitude_meters = subpoint.elevation.m
        x, y, z = position.frame_xyz(itrs).m
        velocity = position.velocity.km_per_s
        velocity_x, velocity_y, velocity_z = velocity
        min_elevation = 0
        sensor_radius_meters = compute_sensor_radius(altitude_meters, min_elevation)
        ecef_position = position.position.m
        ecef_x, ecef_y, ecef_z = ecef_position

        positions.append({
            'name': satellite.name,
            'latitude': lat.degrees,
            'longitude': lon.degrees,
            'altitude': altitude_meters,
            'radius': sensor_radius_meters,
            'velocity': [velocity_x, velocity_y, velocity_z],
            'state': True,
            'time': current_datetime,
            'ecef': [x, y, z]
        })

    return jsonify(positions)

@app.route('/env.js')
def env_js():
    return send_from_directory('.', 'env.js')

if __name__ == '__main__':
    app.run(debug=True, port=8080)