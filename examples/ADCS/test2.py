# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 15:43:15 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, EarthSatellite

# Load the necessary data from Skyfield
ts = load.timescale()
planets = load('de421.bsp')
earth = planets['earth']

# Define the orbital elements of the satellite
line1 = '1 51850U 22021A   23103.42428181  .00000090  00000+0  00000+0 0  9992'
line2 = '51850   0.0114  85.8751 0000446 290.6496 200.5578  1.00271298  4147'

# Define the initial orientation quaternion for the nadir-pointing satellite
q0 = R.from_rotvec(np.radians(-90) * np.array([1, 0, 0])).as_quat()

# Define the time interval and number of steps for the simulation
duration = 86400.0  # duration [s]
step_size = 60.0    # step size [s]
num_steps = int(duration / step_size)

# Create an empty array to store the satellite positions
positions = np.zeros((num_steps, 3))

# Create a Skyfield EarthSatellite object from the orbital elements
satellite = EarthSatellite(line1,line2)

# Loop over each time step and calculate the satellite position
for i in range(num_steps):
    # Calculate the current time
    t = ts.utc(2023, 4, 13, 12, 0, 0) + i * step_size

    # Get the position of the satellite relative to the Earth at the current time
    pos = satellite.at(t).position.km

    # Rotate the position vector to account for the nadir-pointing orientation
    q = q0.copy()
    q = q * R.from_rotvec(np.radians(180) * np.array([1, 0, 0])).as_quat()
    pos_nadir = q.rotate(pos)

    # Add the nadir-pointing position vector to the array of positions
    positions[i] = pos_nadir

    # Update the orientation quaternion for the next time step
    q = q * R.from_quat([pos_nadir[2], -pos_nadir[1], pos_nadir[0], 0])
    q0 = q.normalized()

# Print the final position vector in km
print(positions[-1])
