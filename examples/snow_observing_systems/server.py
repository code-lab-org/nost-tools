from flask import Flask, jsonify, send_from_directory
from skyfield.api import EarthSatellite, load, utc
from datetime import datetime, timezone
from skyfield.api import wgs84
import numpy as np

app = Flask(__name__)

# Load the timescale
ts = load.timescale()

# Define the satellite name
satellite_name = "CAPELLA-14 (ACADIA-4)"

# Load the TLE data for satellite
capella = EarthSatellite(
    "1 59444U 24066C   24255.58733490  .00027683  00000+0  27717-2 0  9992",
    "2 59444  45.6105 355.6094 0002469 338.3298  21.7475 14.91016875 15732",
    satellite_name,
    ts=ts,
)

def compute_sensor_radius(altitude, min_elevation):
    """
    Computes the sensor radius for a satellite at current altitude given minimum elevation constraints.

    Args:
        altitude (float): Altitude (meters) above surface of the observation
        min_elevation (float): Minimum angle (degrees) with horizon for visibility

    Returns:
        float : sensor_radius
            The radius (meters) of the nadir pointing sensors circular view of observation
    """
    earth_equatorial_radius = 6378137.0
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    # eta is the nadir angle between the sub-satellite direction and the target location on the surface
    eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
    # calculate swath width half angle from trigonometry
    sw_HalfAngle = 90 - eta - min_elevation
    if sw_HalfAngle < 0.0:
        return 0.0
    return earth_mean_radius * np.radians(sw_HalfAngle)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/get_position')
def get_position():

    # Get the current time
    # current_datetime = datetime.now().replace(tzinfo=utc)
    current_datetime = datetime.now(timezone.utc)
    
    # Get the position of Capella at the current time
    position = capella.at(ts.from_datetime(current_datetime))

    # Get the latitude, longitude, and altitude of the satellite
    lat, lon = wgs84.latlon_of(position)
    height = wgs84.height_of(position)
    altitude_meters = height.m
    
    # Calculate velocity
    velocity = position.velocity.km_per_s

    # Split the velocity ndarray into x, y, z components
    velocity_x, velocity_y, velocity_z = velocity

    # Calculate the sensor radius
    min_elevation = 10
    sensor_radius_meters = compute_sensor_radius(altitude_meters, min_elevation)

    return jsonify({
        'name': satellite_name,
        'latitude': lat.degrees,
        'longitude': lon.degrees,
        'altitude': altitude_meters,
        'radius': sensor_radius_meters,
        'velocity': [velocity_x, velocity_y, velocity_z],
        'state': True, # Update logic
        'time': current_datetime
    })

@app.route('/env.js')
def env_js():
    return send_from_directory('.', 'env.js')

if __name__ == '__main__':
    app.run(debug=True)