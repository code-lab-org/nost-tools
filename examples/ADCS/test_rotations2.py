# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 18:10:44 2023

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

# # Define the initial orientation of the satellite (pointing towards the negative z-axis)
init_orientation = R.from_euler('xyz', [0, 0, 0], degrees=True).as_quat()  # body axes

r = [0, 7500, 0]
v = [3000, 0, 0]

# Normalize position and velocity vectors
position_norm = r / np.linalg.norm(r)
velocity_norm = v / np.linalg.norm(v)

# Calculate the cross product of the normalized position and velocity vectors ()
cross_product = np.cross(position_norm, velocity_norm)

# Normalize the cross product vector
cross_norm = cross_product / np.linalg.norm(cross_product)

# Calculate the cross product of the normalized velocity vector and the normalized cross product vector
cross2_product = np.cross(velocity_norm, cross_norm)

# Normalize the second cross product vector
cross2_norm = cross2_product / np.linalg.norm(cross2_product)

# Calculate the cross product of the normalized cross product vector and the normalized second cross product vector
cross3_norm = np.cross(cross_norm, cross2_norm)

# Assemble the direction cosine matrix
dcm = np.array([cross2_norm, cross3_norm, cross_norm]).T

# set up rotation
# r = R.from_matrix(dcm).as_quat

# Define the rotation angle and axis
angle = np.deg2rad(10)
axis = np.array([1, 0, 0])

# Create a rotation object using the angle-axis representation
r = R.from_rotvec(angle * axis)

# Convert the rotation object to a quaternion
q = r.as_quat()

# Apply the rotation to the DCM
new_dcm = r.apply(dcm)

# Convert the new DCM to a quaternion
new_q = R.from_matrix(new_dcm).as_quat()

new_euler = R.from_matrix(new_dcm).as_rotvec()

print("Original DCM:\n", dcm)
print("New DCM:\n", new_dcm)
print("Quaternion representing the rotation:\n", q)
print("New quaternion:\n", new_q)
print("New euler:\n", new_euler)








# set up DCM rotation

# apply DCM rotation

# set up attitude rotation

# apply attitude rotation

# r2 = R.from_euler('y', 90, degrees=True)
# initnew = r2.apply(vel)



# specific angular momentum
# h = np.cross(pos, vel)





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
