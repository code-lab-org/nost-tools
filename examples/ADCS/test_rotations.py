# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 13:54:00 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, Topos, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta

# Load the Earth's gravitational field model and the TLE data for the satellite
ts = load.timescale()

# GOES 18 tles
line1 = '1 51850U 22021A   23103.96072472  .00000087  00000+0  00000+0 0  9995'
line2 = '2 51850   0.0319  43.0117 0000436 329.8306  37.8882  1.00271539  4170'

# Quetz sat
# line1 = '1 29155U 06018A   23104.14393936  .00000024  00000+0  00000+0 0  9999'
# line2 = '2 29155   1.3691  92.0151 0001511 167.1063  56.5698  1.00277598 31747'

# TDRS 13
# line1 = '1 42915U 17047A   23109.36291025 -.00000116  00000+0  00000+0 0  9990'
# line2 = '2 42915   4.0741 337.0567 0017562 107.8120 241.4748  1.00272525 20769'

# Create an EarthSatellite object from the TLE data
satellite = EarthSatellite(line1, line2,'GOES 18')


# Define the time range for the simulation
start_time = datetime(2020, 4, 14, 7, 20, 0, tzinfo=timezone.utc)
current_time = start_time
end_time = datetime(2020, 4, 15, 8, 20, 0, tzinfo=timezone.utc)
duration = (end_time - start_time).total_seconds()
step = 30 # seconds
num_steps = int(duration/step)


# Initialize the satellite's position and orientation arrays
# positions= np.zeros((num_steps, 3))
# #positionsTopo = np.zeros((num_steps, 3))
# velocities = np.zeros((num_steps, 3))
# orientations = np.zeros((num_steps, 3))
# bxs = np.zeros((num_steps, 3))
# bys = np.zeros((num_steps, 3))
# bzs = np.zeros((num_steps, 3))
# orthcheck = np.zeros((num_steps))

# # Define the initial orientation of the satellite (pointing towards the negative z-axis)
# init_orientation = R.from_euler('xyz', [0, 0, 0], degrees=True).as_quat()

# # Define the initial attitude in inertial frame
# init_position = satellite.at(ts.utc(start_time)).position.km
# init_velocity = satellite.at(ts.utc(start_time)).velocity.km_per_s
# posMag = np.linalg.norm(init_position)                        # position magnitude
# velMag = np.linalg.norm(init_velocity)                        # velocity magnitude  
# b_x = init_velocity/velMag                                    # body x-axis along velocity vector
# b_z = init_position/posMag                                    # body z-axis nadir pointing
# b_y = np.cross(b_x,b_z)                                       # body y-axis normal to orbital plane

# dcm0 = np.stack([b_x, b_y, b_z])                              # initial rotation axis

# r = R.from_matrix(dcm0)

# with dummy vectors

pos = [0, 1000, 0]
vel = [3, 0, 0]
posMag = np.linalg.norm(pos)                        # position magnitude
velMag = np.linalg.norm(vel)                        # velocity magnitude  
b_x = vel/velMag                                    # body x-axis along velocity vector
b_z = pos/posMag                                    # body z-axis nadir pointing
b_y = np.cross(b_x,b_z)                                       # body y-axis normal to orbital plane

dcm0 = np.stack([b_x, b_y, b_z])                              # initial rotation axis

r = R.from_matrix(dcm0)





# # Simulate the satellite's position and orientation over time
# for i in range(num_steps):
    
#     time = ts.utc(current_time)
#     # inertial position 
#     position = satellite.at(time).position.km    # position in GCRS/J2000
#     positions[i] = position
#     # topocentric position
#     # topocentric = wgs84.geographic_position_of(satellite.at(time))
#     # positionsTopo = topocentric
    
#     # Velocity 
#     velocity = satellite.at(time).velocity.km_per_s
#     velocities[i] = velocity
    
#     # specific angular momentum
#     h = np.cross(position, velocity)
    
#     posMag = np.linalg.norm(position)            # position magnitude
#     velMag = np.linalg.norm(velocity)            # velocity magnitude  
#     b_x = velocity/velMag                        # body x-axis along velocity vector
#     b_z = position/posMag                        # body z-axis nadir pointing
#     b_y = np.cross(b_x,b_z)                      # body y-axis normal to orbital plane
    
#     orthcheck[i] = np.dot(b_x,b_z)
    
#     bxs[i] = b_x
#     bys[i] = b_y
#     bzs[i] = b_z

    




    
    # current_time = current_time + timedelta(0,step)

    # Print 
    #print(h)

