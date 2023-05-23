# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 18:10:44 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.integrate import ode

# from skyfield.api import load, Topos, EarthSatellite, wgs84
# from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt

# import skinematics as skin


# Define initial state of satellite
# mass of single cubesat cube (kg)
cubeMass = 2
# length of single cubesat cube (m)
cubeLength = 0.1
# 6U cubesat inertia tensor
# I = np.diag([cubeMass/12*((1*cubeLength)**2+(2*cubeLength)**2),
#              cubeMass/12*((1*cubeLength)**2+(3*cubeLength) ** 2),
#              cubeMass/12*((2*cubeLength)**2+(3*cubeLength)**2)])

# from Wie
# I = np.array([[1200, 100, -200],[100, 2200, 300],[-200, 300, 3100]])

# from  Sidi book
I = np.diag([100, 100, 100])
currentQuat = np.array([0.0, 0.0, 0.0, 1.0])  # x,y,z,w
rot = R.from_euler('xyz', [45,0,0], degrees=True)
targetQuat = (R.as_quat(rot))
#targetQuat = np.array([0.258819, 0, 0, 0.965926])
Kp = np.array([1000, 1000, 1000])  # proportional gain
# Ki = np.array([0.1, 0.1, 0.1])       # integral gain
Kd = np.array([1900, 10, 10])  # derivative gain

# initial angular velocity in body frame
w = np.array([0, 0,0])
alpha = np.array([0, 0, 0])
eulerRad = np.array([0, 0, 0])

# Define reaction wheel specifications
Iw = np.array([0.1, 0.1, 0.1])  # moment of inertia of each wheel
max_torque = np.array([1, 1, 1])  # maximum torque each wheel can produce

# Define simulation parameters
dt = .1  # time step
t_final = 60  # final time
steps = int(t_final / dt)

# Initialize arrays
alpha_hist = np.zeros((steps, 3))
euler_hist = np.zeros((steps, 3))
w_hist = np.zeros((steps, 3))
q_hist = np.zeros((steps, 4))
T_hist = np.zeros((steps, 3))
errorQuat = np.zeros(4)
error_hist = np.zeros((steps, 4))
T_c = np.zeros(3)


# Calculate error between current quat and desired quat (Wie style)
def att_error(currentQuat, targetQuat):
    qT = np.array(
        [
            [targetQuat[3], targetQuat[2], -targetQuat[1], -targetQuat[0]],
            [-targetQuat[2], targetQuat[3], targetQuat[0], -targetQuat[1]],
            [targetQuat[1], -targetQuat[0], targetQuat[3], -targetQuat[2]],
            [targetQuat[0], targetQuat[1], targetQuat[2], targetQuat[3]],
        ]
    )
    qB = np.array([currentQuat[0], currentQuat[1], currentQuat[2], currentQuat[3]])
    errorQuat = np.matmul(qT, qB)

    return errorQuat


# Calculate torque produced by reaction wheels 
def control_torque(errorQuat, Kp, Kd, w):  #Sidi
    
    T_c[0] = -(2 * Kp[0] * errorQuat[0] * errorQuat[3] + Kd[0] * w[0])
    T_c[1] = -(2 * Kp[1] * errorQuat[1] * errorQuat[3] + Kd[1] * w[1])
    T_c[2] = -(2 * Kp[2] * errorQuat[2] * errorQuat[3] + Kd[2] * w[2])

    return T_c


def quaternion_product(currentQuat, qwdt):
    x0 = currentQuat[0]
    y0 = currentQuat[1]
    z0 = currentQuat[2]
    w0 = currentQuat[3]

    x1 = qwdt[0]
    y1 = qwdt[1]
    z1 = qwdt[2]
    w1 = qwdt[3]

    xn = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
    yn = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
    zn = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1
    wn = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
    
    currentQuat = np.array([xn,yn,zn,wn])

    return currentQuat


# Run simulation
for i in range(steps):
    # Calculate error quaternion
    errorQuat = att_error(currentQuat, targetQuat)

    # Calculate torque produced by reaction wheels
    T_c = control_torque(errorQuat, Kp, Kd, w)

    # Update angular velocity, euler angles, and quaternion
    alpha = np.matmul(np.linalg.inv(I), T_c)
    w = w + alpha * dt
    eulerRad = eulerRad + w * dt
    euler = np.degrees(eulerRad)
    # currentQuat = taylorIntegrate(w, currentQuat, dt)

    #     # from Sola
    # qwdt = [np.cos(np.linalg.norm(w)*dt/2)],[((w/np.linalg.norm(w))*np.sin(np.linalg.norm(w)*dt/2))]
    qwdt = np.array(
        [
            ((w[0] / np.linalg.norm(w)) * np.sin(np.linalg.norm(w) * dt / 2)),
            ((w[1] / np.linalg.norm(w)) * np.sin(np.linalg.norm(w) * dt / 2)),
            ((w[2] / np.linalg.norm(w)) * np.sin(np.linalg.norm(w) * dt / 2)),
            np.cos(np.linalg.norm(w) * dt / 2)
        ]
    )
    currentQuat = quaternion_product(currentQuat, qwdt)

    #     currentQuat = currentQuat + 0.5*currentQuat*np.array([w[0], w[1], w[2], 0])*dt
    #     # currentQuat = currentQuat / np.linalg.norm(currentQuat)
    #     # euler = R.from_quat(currentQuat).as_euler('zyx', degrees=True)

    #     # Store results
    alpha_hist[i, :] = alpha
    w_hist[i, :] = w
    euler_hist[i, :] = euler
    q_hist[i, :] = currentQuat
    T_hist[i, :] = T_c
    error_hist[i, :] = errorQuat = errorQuat

plt.figure(1)
plt.plot(w_hist[:, 0])
plt.title("omega")
plt.show

plt.figure(2)
plt.plot(alpha_hist[:, 0])
plt.title("alpha")
plt.show

plt.figure(3)
plt.subplot(2, 2, 1)
plt.plot(euler_hist[:, 0])
plt.title("euler X")


plt.subplot(2, 2, 2)
plt.plot(euler_hist[:, 1])
plt.title("euler Y")


plt.subplot(2, 2,3)
plt.plot(euler_hist[:, 2])
plt.title("euler Z")
plt.tight_layout()
plt.show




# print("Quaternion for Cesium", quat[0], ",", quat[1], ",", quat[2], ",", quat[3])
