# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 15:15:07 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, Topos, EarthSatellite
from datetime import datetime, timezone, timedelta
from sgp4.api import Satrec, WGS84

# Load the Earth's gravitational field model and the TLE data for the satellite
ts = load.timescale()

# create satellite from SatR

satrec = Satrec()
satrec.sgp4init(
    WGS84,           # gravity model
    'i',             # 'a' = old AFSPC mode, 'i' = improved mode
    125,               # satnum: Satellite number
    18441.785,       # epoch: days since 1949 December 31 00:00 UT
    0,               # bstar: drag coefficient (/earth radii)
    0,               # ndot: ballistic coefficient (revs/day)
    0.0,             # nddot: second derivative of mean motion (revs/day^3)
    0,               # ecco: eccentricity
    0,               # argpo: argument of perigee (radians)
    0,               # inclo: inclination (radians)
    0,               # mo: mean anomaly (radians)
    0.1,               # no_kozai: mean motion (radians/minute)
    0                # nodeo: right ascension of ascending node (radians)
)

# Create an EarthSatellite object from satrec
satellite = EarthSatellite.from_satrec(satrec,ts)

# Define the initial orientation of the satellite (pointing towards the negative z-axis)
init_orientation = R.from_euler('xyz', [0, 0, 180], degrees=True).as_quat()

# Define the time range for the simulation
start_time = datetime(2020, 4, 14, 7, 20, 0, tzinfo=timezone.utc)
current_time = start_time
end_time = datetime(2020, 4, 14, 10, 20, 0, tzinfo=timezone.utc)
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
    # rotation_quat = R.from_rotvec(rotation_angle * rotation_axis).as_quat()
    # new_orientation = R.from_quat(rotation_quat) * R.from_quat(init_orientation)
    # orientations[i] = new_orientation.as_euler('xyz', degrees=True)
    
    current_time = current_time + timedelta(0,step)

# Print the final orientation of the satellite
print('Final orientation:', orientations[-1])