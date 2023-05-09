# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 18:10:44 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, Topos, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt


# Define the position and velocity vectors
r = np.array([0, 0, 7189833])
v = np.array([7500, 0, 0])

# Define initial state of satellite
# mass of single cubesat cube (kg)
cubeMass = 2
# length of single cubesat cube (m)
cubeLength = 0.1
# 6U cubesat inertia tensor
# I = np.diag([cubeMass/12*((1*cubeLength)**2+(2*cubeLength)**2),
#              cubeMass/12*((1*cubeLength)**2+(3*cubeLength) ** 2),
#              cubeMass/12*((2*cubeLength)**2+(3*cubeLength)**2)])

#from Wie
#I = np.array([[1200, 100, -200],[100, 2200, 300],[-200, 300, 3100]])

I = np.diag([1000, 500, 700])
currentQuat = np.array([0,0,0,1])
rot = R.from_euler('z', [-60], degrees=True)
targetQuat = np.array([0.,	0.,	-0.5,	.866025403784438707])

# initial angular velocity in body frame
w = np.array([0, 0, 0])
alpha = np.array([0, 0, 0])
eulerRad = np.array([0, 0, 0])
#euler = R.from_quat(currentQuat).as_euler('xyz', degrees=True)                           # initial euler angles

# Define PID controller gains
Kp = np.array([1000, 500, 70])         # proportional gain
# Ki = np.array([0.1, 0.1, 0.1])       # integral gain
Kd = np.array([2000, 500, 10])       # derivative gain

# Define reaction wheel specifications
Iw = np.array([0.1, 0.1, 0.1])    # moment of inertia of each wheel
max_torque = np.array([1, 1, 1])  # maximum torque each wheel can produce

# Define simulation parameters
dt = 1   # time step
t_final = 60   # final time
steps = int(t_final/dt)

# Initialize arrays
alpha_hist = np.zeros((steps, 3))
euler_hist = np.zeros((steps, 3))
w_hist = np.zeros((steps, 3))
q_hist = np.zeros((steps, 4))
torque_hist = np.zeros((steps, 3))
errorQuat = np.zeros(4)
T_c = np.zeros(3)

# setting up reference coordinate frame
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
# targetQuat = R.from_matrix(R_bo).as_quat()
# targetQuat = np.array([0, -0.34202, 0, 0.93969])


def quaternion_multiply(Q0,Q1):
    """
    Multiplies two quaternions.
 
    Input
    :param Q0: A 4 element array containing the first quaternion (q01,q11,q21,q31) 
    :param Q1: A 4 element array containing the second quaternion (q02,q12,q22,q32) 
 
    Output
    :return: A 4 element array containing the final quaternion (q03,q13,q23,q33) 
 
    """
    # Extract the values from Q0
    x0 = Q0[0]
    y0 = Q0[1]
    z0 = Q0[2]
    w0 = Q0[3]
     
    # Extract the values from Q1
    x1 = Q1[0]
    y1 = Q1[1]
    z1 = Q1[2]
    w1 = Q1[3]
     
    # Computer the product of the two quaternions, term by term
    Q0Q1_w = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
    Q0Q1_x = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
    Q0Q1_y = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
    Q0Q1_z = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1
     
    # Create a 4 element array containing the final quaternion
    final_quaternion = np.array([Q0Q1_w, Q0Q1_x, Q0Q1_y, Q0Q1_z])
     
    # Return a 4 element array containing the final quaternion (q02,q12,q22,q32) 
    return final_quaternion


# Calculate error between current quat and desired quat 
def att_error(currentQuat, targetQuat):

    qT = np.array([[targetQuat[3], targetQuat[2], -targetQuat[1], targetQuat[0]],
                  [-targetQuat[2], targetQuat[3], targetQuat[0], targetQuat[1]],
                  [targetQuat[1], -targetQuat[0], targetQuat[3], targetQuat[2]],
                  [-targetQuat[0], -targetQuat[1], -targetQuat[2], targetQuat[3]]])
    qB = np.array([-currentQuat[0], -currentQuat[1], -currentQuat[2], currentQuat[3]])
    errorQuat = np.matmul(qT, qB)

    return errorQuat

# Calculate torque produced by reaction wheels (in body frame?)


def control_torque(errorQuat, Kp, Kd, w):

    T_c[0] = 2*Kp[0]*errorQuat[0]*errorQuat[3] + Kd[0]*w[0]
    T_c[1] = 2*Kp[0]*errorQuat[1]*errorQuat[3] + Kd[1]*w[1]
    T_c[2] = 2*Kp[0]*errorQuat[2]*errorQuat[3] + Kd[2]*w[2]

    return T_c


omegaPrime = np.array([[0, w[2], -w[1], w[0]],
                       [-w[2], 0, w[0], w[1]],
                       [w[1], -w[0], 0, w[2]],
                       [-w[0], -w[1], -w[2], 0]])

# Run simulation
for i in range(steps):
    # Calculate error quaternion
    errorQuat = att_error(currentQuat, targetQuat)

    # Calculate torque produced by reaction wheels
    T_c = control_torque(errorQuat, Kp, Kd, w)

    # Update angular velocity, euler angles, and quaternion
    alpha = np.matmul(np.linalg.inv(I), T_c) 
    w = w + alpha*dt
    eulerRad = eulerRad + w*dt +0.5*alpha*dt**2
    euler = np.degrees(eulerRad)

    
    # from Sola
    # qwdt = [np.cos(np.linalg.norm(w)*dt/2)],[((w/np.linalg.norm(w))*np.sin(np.linalg.norm(w)*dt/2))]
    # qwdt = np.array([np.cos(np.linalg.norm(w)*dt/2),((w[0]/np.linalg.norm(w))*np.sin(np.linalg.norm(w)*dt/2)),((w[1]/np.linalg.norm(w))*np.sin(np.linalg.norm(w)*dt/2)),((w[2]/np.linalg.norm(w))*np.sin(np.linalg.norm(w)*dt/2))])
    # currentQuat = quaternion_multiply(currentQuat, qwdt)
    
    #qdot = 
    
    # currentQuat = currentQuat + 0.5*currentQuat*np.array([w[0], w[1], w[2], 0])*dt
    # currentQuat = currentQuat / np.linalg.norm(currentQuat)
    # euler = R.from_quat(currentQuat).as_euler('zyx', degrees=True)

    # Store results
    alpha_hist[i, :] = alpha
    w_hist[i, :] = w
    euler_hist[i, :] = euler
    q_hist[i, :] = currentQuat

    torque_hist[i, :] = T_c

plt.plot(euler_hist[:, 2])
plt.show


# print("Quaternion for Cesium", quat[0], ",", quat[1], ",", quat[2], ",", quat[3])
