# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 16:33:35 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, Topos, EarthSatellite
from datetime import datetime, timezone, timedelta

# Load the Earth's gravitational field model and the TLE data for the satellite
ts = load.timescale()
planets = load('de421.bsp')

# GOES 18 tles
# line1 = '1 51850U 22021A   23103.96072472  .00000087  00000+0  00000+0 0  9995'
# line2 = '2 51850   0.0319  43.0117 0000436 329.8306  37.8882  1.00271539  4170'

# Quetz sat
line1 = '1 29155U 06018A   23104.14393936  .00000024  00000+0  00000+0 0  9999'
line2 = '2 29155   1.3691  92.0151 0001511 167.1063  56.5698  1.00277598 31747'



# Define the observer's location
observer = Topos(latitude_degrees=0, longitude_degrees=0)

# Create an EarthSatellite object from the TLE data
satellite = EarthSatellite(line1, line2,'GOES 18')

# Define the initial orientation of the satellite (pointing towards the negative z-axis)
init_orientation = R.from_euler('xyz', [0, 0, 180], degrees=True).as_quat()

# Define the time range for the simulation
start_time = datetime(2020, 4, 14, 7, 20, 0, tzinfo=timezone.utc)
current_time = start_time
end_time = datetime(2020, 4, 15, 8, 20, 0, tzinfo=timezone.utc)
duration = (end_time - start_time).total_seconds()
step = 10 # seconds
num_steps = int(duration/step)


# Initialize the satellite's position and orientation arrays
positions = np.zeros((num_steps, 3))
velocities = np.zeros((num_steps, 3))
orientations = np.zeros((num_steps, 3))
icrs = np.zeros((num_steps, 3))



# Simulate the satellite's position and orientation over time
for i in range(num_steps):
    
    time = ts.utc(current_time)
    # Get the satellite's position relative to the observer
    satellite_position = satellite.at(time).position.km
    positions[i] = satellite_position
    inertial_position = satellite.at(time).ecliptic_position().km
    icrs[i] = inertial_position

    # Get the satellite's velocity relative to the observer
    satellite_velocity = satellite.at(time).velocity.m_per_s
    velocities[i] = satellite_velocity

    # Calculate the new orientation of the satellite based on its velocity vector
    velocity_direction = satellite_velocity / np.linalg.norm(satellite_velocity)
    if np.allclose(velocity_direction, [0, 0, -1]):
        # If the velocity direction is exactly opposite to the negative z-axis,
        # choose the x-axis or y-axis as the rotation axis (whichever is closer to
        # being perpendicular to the velocity direction)
        if np.abs(velocity_direction[0]) >= np.abs(velocity_direction[1]):
            rotation_axis = np.array([velocity_direction[0], 0, 0])
        else:
            rotation_axis = np.array([0, velocity_direction[1], 0])
    else:
        rotation_axis = np.cross(np.array([0, 0, -1]), velocity_direction)
    rotation_angle = np.arccos(np.dot(np.array([0, 0, -1]), velocity_direction))
    rotation_quat = R.from_rotvec(rotation_angle * rotation_axis).as_quat()
    new_orientation = R.from_quat(rotation_quat) * R.from_quat(init_orientation)
    orientations[i] = new_orientation.as_euler('xyz', degrees=True)
    
    current_time = current_time + timedelta(0,step)

# Print the final orientation of the satellite
print('Final orientation:', orientations[-1])

