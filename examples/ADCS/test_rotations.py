# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 18:10:44 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, Topos, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta


# Define the position and velocity vectors
r = np.array([
            0,
            0,
            7189832.554930149
])
v = np.array([
    7500,
    0,
    0
])

# Define initial state of satellite
cubeMass = 2                                                       # mass of single cubesat cube (kg)
cubeLength = 0.1                                                   # length of single cubesat cube (m)
# 6U cubesat inertia tensor                                    
I = np.diag([cubeMass/12*((1*cubeLength)**2+(2*cubeLength)**2), 
              cubeMass/12*((1*cubeLength)**2+(3*cubeLength)** 2), 
              cubeMass/12*((2*cubeLength)**2+(3*cubeLength)**2)])   
currentQuat = np.array([0.3826834323650898,                         # initial attitude quaternion (45 deg roll about x)
                        0.0, 
                        0.0, 
                        0.9238795325112867])     
w = np.array([0, 0, 0])                                            # initial angular velocity in body frame
euler = np.array([0,0,0])                                          # initial euler angles 

# Define PID controller gains
Kp = np.array([1, 1, 1])         # proportional gain
# Ki = np.array([0.1, 0.1, 0.1])   # integral gain
Kd = np.array([0.1, 0.1, 0.1])   # derivative gain

# Define reaction wheel specifications
Iw = np.array([0.1, 0.1, 0.1])    # moment of inertia of each wheel
max_torque = np.array([1, 1, 1])  # maximum torque each wheel can produce

# Define simulation parameters
dt = 1   # time step
t_final = 100   # final time

# Initialize arrays
euler_hist = np.zeros((t_final,3))
q_hist = np.zeros((t_final, 4))
w_hist = np.zeros((t_final, 3))
torque_hist = np.zeros((t_final, 3))
errorQuat = np.zeros(4)
T_c = np.zeros(3)

## setting up reference coordinate frame
# Calculate the specific angular momentum vector
h = np.cross(r, v)
# Calculate the unit vectors for the reference x, y, and z axes
y_r = h / np.linalg.norm(h)
z_r = r / np.linalg.norm(r) 
x_r = np.cross(y_r, z_r)
# Calculate the rotation matrix from the reference to the inertial frame (body to inertial?)
R_bo = np.vstack((x_r, y_r, z_r)).T
# Calculate the rotation matrix from the inertial to the body frame
# R_ib = R_bo.T
# Convert the rotation matrix to a quaternion
targetQuat = R.from_matrix(R_bo).as_quat()



# Calculate error between current quat and desired quat
def att_error(currentQuat, targetQuat):
    
    qT = np.array([[targetQuat[3], targetQuat[2], -targetQuat[1], targetQuat[0]],
                  [-targetQuat[2], targetQuat[3], targetQuat[0], targetQuat[1]],
                  [targetQuat[1], -targetQuat[0], targetQuat[3], targetQuat[2]],
                  [-targetQuat[0], -targetQuat[1], -targetQuat[2], targetQuat[3]]])
    qB = np.array([-currentQuat[0], -currentQuat[1], -currentQuat[2], currentQuat[3]])
    errorQuat = np.matmul(qT,qB)
    
    return errorQuat

# Calculate torque produced by reaction wheels (in body frame?)
def control_torque(errorQuat, Kp, Kd, w):
    
    T_c[0] = 2*Kp[0]*errorQuat[0]*errorQuat[3] + Kd[0]*w[0]
    T_c[1] = 2*Kp[0]*errorQuat[1]*errorQuat[3] + Kd[1]*w[1]
    T_c[2] = 2*Kp[0]*errorQuat[2]*errorQuat[3] + Kd[2]*w[2]
    
    return T_c


# Run simulation
for i in range(t_final):
    # Calculate error quaternion
    errorQuat = att_error(currentQuat, targetQuat)

    # Calculate torque produced by reaction wheels
    T_c = control_torque(errorQuat, Kp, Kd, w)

    # Update angular velocity, euler angles, and quaternion 
    w = np.matmul(np.linalg.inv(I), T_c)
    euler = w*dt                                 
    currentQuat = currentQuat + 0.5*np.array([w[0],w[1],w[2],0])*dt
    currentQuat = currentQuat / np.linalg.norm(currentQuat)

    # Store results
    euler_hist[i,:] = euler
    q_hist[i,:] = currentQuat
    w_hist[i,:] = w
    torque_hist[i,:] = T_c


# print("Quaternion for Cesium", quat[0], ",", quat[1], ",", quat[2], ",", quat[3])
