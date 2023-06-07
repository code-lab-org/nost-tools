# -*- coding: utf-8 -*-
"""
Created on Wed May 31 15:55:14 2023

@author: brian
"""

from skyfield.api import EarthSatellite, load, wgs84
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from datetime import timedelta


culm = []
T_c = []

# Name(s) of satellite(s) used in Celestrak database
name = "TERRA"

activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
activesats = load.tle_file(activesats_url, reload=False)
by_name = {sat.name: sat for sat in activesats}

satellite=by_name[name]

ts = load.timescale()
targetLoc = wgs84.latlon(40.7440, -74.0324)
t_start = ts.utc(2014, 1, 23)
t_length = timedelta(minutes=2400)
t_end = t_start + t_length


t, events = satellite.find_events(targetLoc, t_start, t_end, altitude_degrees=15.0)
eventZip = list(zip(t,events))
df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
culmTimes = df.loc[df["Event"]==1]

# for i in range(culmTimes):
#     df["culmPosX"] = satellite.at(culmTimes)(culmTimes.iloc[0]["Time"]).position.m[0]

geocentric = satellite.at(t_start)
pos = geocentric.position.m
vel = geocentric.velocity.m_per_s

# initial nadir-pointing attitude 
h = np.cross(pos, vel)
# Calculate the unit vectors for the body x, y, and z axes
b_y = h / np.linalg.norm(h)                   # body y-axis normal to orbital plane
b_z = pos / np.linalg.norm(pos)              # body z-axis nadir pointing
b_x0 = np.cross(b_y, b_z)
b_x = b_x0 / np.linalg.norm(b_x0)             # body x-axis along velocity vector
# Create the rotation matrix from the body to the inertial frame
R_bi = np.vstack((b_x, b_y, b_z)).T
att = R.from_matrix(R_bi).as_quat() # np.array([0,0,0,1])
targetQuat = R.from_matrix(R_bi).as_quat()     # initial nadir-pointing quaternion from inertial to body coordinates
# print("ATT QUAT IS0!!!!!!!!!", att)
omega = np.array([0,0,0])               # initial rotational velocity

time = t_start

# find target quaternion at culmination from ground location
def update_target_attitude(self, next_pos, next_vel, targetLoc, t_start, t_end):
    
    #nadir-pointing attitude 
    h = np.cross(next_pos, next_vel)
    # Calculate the unit vectors for the body x, y, and z axes
    b_y = h / np.linalg.norm(h)
    b_z = next_pos / np.linalg.norm(next_pos)
    b_x0 = np.cross(b_y, b_z)
    b_x = b_x0 / np.linalg.norm(b_x0)
    # Create the rotation matrix from the body to the inertial frame
    R_bi = np.vstack((b_x, b_y, b_z)).T
    #targetQuat = R.from_matrix(R_bi).as_quat()
    
    # Find culmination times and positions
    t, events = satellite.find_events(targetLoc, t_start, t_end, altitude_degrees=15.0)
    eventZip = list(zip(t,events))
    df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
    culmTimes = df.loc[df["Event"]==1]
    
    culmGeo = satellite.at(culmTimes.iloc[0]["Time"])    # skyfield Geocentric Position object at first culmination time
    
    culmTime = (culmTimes.iloc[0]["Time"]).utc_iso()
    culmPos = culmGeo.position.m
    targetPos = targetLoc.at(culmTimes.iloc[0]["Time"]).position.m
    culmVel = culmGeo.velocity.m_per_s
    
    # find roll angle between nadir vector and target
    culmUnitVec = culmPos/np.linalg.norm(culmPos)      
    direction = culmPos - targetPos
    dirUnit = direction/np.linalg.norm(direction)
    
    rollAngle = np.arccos(np.dot(dirUnit, culmUnitVec))
    
    targetRot = R.from_matrix(R_bi)*R.from_euler('x', rollAngle)
    targetQuat = targetRot.as_quat()
    print("ROLLLLLLLLLLLLLLLLLLLLLL!!!!!",rollAngle)
    
    print("The TARGET QUAT ISSSSS!!!!!",targetQuat)
    
    return targetQuat
        
# Calculate error between current quat and desired quat (Wie style)
def att_error(self, next_pos, next_vel):
    
    targetQuat = update_target_attitude(next_pos, next_vel, targetLoc, t_start, t_end)
    # print("The TARGET QUAT ISSSSS!!!!!",targetQuat)
    
    
    qT = np.array(
        [
            [targetQuat[3], targetQuat[2], -targetQuat[1], -targetQuat[0]],
            [-targetQuat[2], targetQuat[3], targetQuat[0], -targetQuat[1]],
            [targetQuat[1], -targetQuat[0], targetQuat[3], -targetQuat[2]],
            [targetQuat[0], targetQuat[1], targetQuat[2], targetQuat[3]],
        ]
    )
    qB = np.array([att[0], att[1], att[2], att[3]])
    
    
    errorQuat = np.matmul(qT, qB)
    
    print("ERROR QUAT IS!!!!!!!!!", errorQuat)
    # print("ATT QUAT IS1!!!!!!!!!", att)

    return errorQuat


# Calculate torque produced by reaction wheels 
def control_torque(self, errorQuat, Kp, Kd):  #Sidi
    
    T_c[0] = -(2 * Kp[0] * errorQuat[0] * errorQuat[3] + Kd[0] * omega[0])
    T_c[1] = -(2 * Kp[1] * errorQuat[1] * errorQuat[3] + Kd[1] * omega[1])
    T_c[2] = -(2 * Kp[2] * errorQuat[2] * errorQuat[3] + Kd[2] * omega[2])
    
    # print("TTOTOTOTOTOTOTORQUE", T_c)

    return T_c


def quaternion_product(self, qwdt):
   
    x0 = att[0]
    y0 = att[1]
    z0 = att[2]
    w0 = att[3]

    x1 = qwdt[0]
    y1 = qwdt[1]
    z1 = qwdt[2]
    w1 = qwdt[3]

    xn = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
    yn = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
    zn = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1
    wn = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
    
    att = np.array([xn,yn,zn,wn])
    
    print("ATT QUAT IS2!!!!!!!!!", att)

    return att

def update_attitude(self, time_step, pos, vel):         
  
    # Calculate error quaternion
    errorQuat = att_error(pos, vel)
    
    # Calculate torque produced by reaction wheels
    T_c = control_torque(errorQuat, Kp, Kd)
    
    # Update angular velocity, euler angles, and quaternion
    alpha = np.matmul(np.linalg.inv(I), T_c)
    omega = omega + alpha * dt
    # eulerRad = eulerRad + omega * time_step
    # euler = np.degrees(eulerRad)
    qwdt = np.array(
        [
            ((omega[0] / np.linalg.norm(omega)) * np.sin(np.linalg.norm(omega) * dt / 2)),
            ((omega[1] / np.linalg.norm(omega)) * np.sin(np.linalg.norm(omega) * dt / 2)),
            ((omega[2] / np.linalg.norm(omega)) * np.sin(np.linalg.norm(omega) * dt / 2)),
            np.cos(np.linalg.norm(omega) * dt / 2)
        ]
    )

    att = quaternion_product(qwdt)
    
    print("ATT QUAT IS3!!!!!!!!!", att)

    return att

for i in 1000:
    
    
    culmTime = (culmTimes.iloc[0]["Time"]).utc_iso()
    culmPos = satellite.at(culmTimes.iloc[0]["Time"]).position.m
    targetPos = targetLoc.at(culmTimes.iloc[0]["Time"]).position.m
    culmUnitVec = culmPos/np.linalg.norm(culmPos)
    targetUnitVec = targetPos/np.linalg.norm(targetPos)
    angle = np.arccos(np.dot(culmUnitVec, targetUnitVec))
    
    r = R.from_euler('x',angle)
    targetQuat = r.as_quat()
    
    time = time + timedelta(minutes=1)
    

    
    

                       
