# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 09:52:11 2023

@author: brian
"""

from skyfield.api import EarthSatellite, load, wgs84, utc
from skyfield.framelib import itrs
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from datetime import datetime, timedelta
from config import PARAMETERS


tle = """
NOAA 21 (JPSS-2)        
1 54234U 22150A   23163.90962243  .00000111  00000+0  73435-4 0  9996
2 54234  98.7164 101.9278 0001563  84.6643 275.4712 14.19552572 30449
"""

lines = tle.strip().splitlines()
ts = load.timescale()

satellite = EarthSatellite(lines[1], lines[2], lines[0])
print(satellite)

t = ts.utc(2023, 6, 23, 50, 25, 50)


geocentric = satellite.at(t)

pos_vel= geocentric.frame_xyz_and_velocity(itrs)
culm_pos = pos_vel[0].m
culm_vel = pos_vel[1].m_per_s
sat_geographical = wgs84.geographic_position_of(geocentric)

targetLoc = wgs84.latlon(sat_geographical.latitude.degrees,  sat_geographical.longitude.degrees+5)


targetPos = targetLoc.itrs_xyz.m
# targetPos = targetLocW.itrs_xyz.m

print("target",targetLoc)
print("satGEO",sat_geographical)
# difference =  sat_geographical.longitude.degrees - targetLoc.longitude.degrees
# print("DIFFFF",difference)

h = np.cross(culm_pos, culm_vel)
# Calculate the unit vectors for the body x, y, and z axes
b_y = h / np.linalg.norm(h)
b_z = culm_pos / np.linalg.norm(culm_pos)
b_x0 = np.cross(b_y, b_z)
b_x = b_x0 / np.linalg.norm(b_x0)

# Calculate the rotation matrix from the body to the inertial frame
R_bi = np.vstack((b_x, b_y, b_z)).T

# Calculate the rotation matrix from the inertial to the body frame
R_ib = R_bi.T
euler_body = R.from_matrix(R_ib).as_euler('xyz')
euler_inertial = R.from_matrix(R_bi).as_euler('xyz')

# Convert the rotation matrix to a quaternion
iQuat = R.from_matrix(R_bi).as_quat()

print("iQuat", iQuat[0], ",", iQuat[1], ",", iQuat[2], ",", iQuat[3])

# find roll angle between nadir vector and target for 1 target

culmUnitVec = culm_pos/np.linalg.norm(culm_pos)
targetUnitVec = targetPos/np.linalg.norm(targetPos)

direction =   culm_pos - targetPos

dirUnit = direction/np.linalg.norm(direction)

rollAngle = np.arccos(np.dot(dirUnit, culmUnitVec)) 

if culm_vel[2] > 0 and sat_geographical.longitude.degrees < targetLoc.longitude.degrees:
    rollAngle = -rollAngle
    
if culm_vel[2] < 0 and sat_geographical.longitude.degrees > targetLoc.longitude.degrees:
    rollAngle = -rollAngle
    
targetRot = R.from_matrix(R_bi)*R.from_euler('x',rollAngle)
rollAngledeg = np.rad2deg(rollAngle)


targetQuat = targetRot.as_quat()

# print("culmination time",culmTime.utc_iso())
print("Roll Angle E", [rollAngledeg])

print("culmination position",[culm_pos])
print("targetQuat", targetQuat[0], ",", targetQuat[1], ",", targetQuat[2], ",", targetQuat[3])




# find roll angle between nadir vector and target for E and W targets
# culmUnitVec = culm_pos/np.linalg.norm(culm_pos)
# targetUnitVecE = targetPosE/np.linalg.norm(targetPosE)
# targetUnitVecW = targetPosW/np.linalg.norm(targetPosW)

# directionE =   culm_pos - targetPosE
# directionW =   culm_pos - targetPosW
# dirUnitE = directionE/np.linalg.norm(directionE)
# dirUnitW = directionW/np.linalg.norm(directionW)

# rollAngleE = np.arccos(np.dot(dirUnitE, culmUnitVec)) 
# rollAngleW = np.arccos(np.dot(dirUnitW, culmUnitVec))



# targetRotE = R.from_matrix(R_bi)*R.from_euler('x',rollAngleE)
# targetRotW = R.from_matrix(R_bi)*R.from_euler('x',rollAngleW)
# rollAngledegE = np.rad2deg(rollAngleE)
# rollAngledegW = np.rad2deg(rollAngleW)
# targetQuatE = targetRotE.as_quat()
# targetQuatW = targetRotW.as_quat()

# # print("culmination time",culmTime.utc_iso())
# print("Roll Angle E", [rollAngledegE])
# print("Roll Angle W", [rollAngledegW])
# print("culmination position",[culm_pos])
# print("targetQuat E", targetQuatE[0], ",", targetQuatE[1], ",", targetQuatE[2], ",", targetQuatE[3])
# print("targetQuat W", targetQuatW[0], ",", targetQuatW[1], ",", targetQuatW[2], ",", targetQuatW[3])
