# -*- coding: utf-8 -*-
"""
Created on Wed May 31 15:55:14 2023

@author: brian
"""

from skyfield.api import EarthSatellite, load, wgs84, utc
from skyfield.framelib import itrs
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from datetime import datetime, timedelta
from config import PARAMETERS

# Name(s) of satellite(s) used in Celestrak database
# name = "SUOMI NPP"
# activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
# activesats = load.tle_file(activesats_url, reload=False)
# by_name = {sat.name: sat for sat in activesats}
# satellite=by_name[name]

# tle = """
# NOAA 21 (JPSS-2)        
# 1 54234U 22150A   23163.90962243  .00000111  00000+0  73435-4 0  9996
# 2 54234  98.7164 101.9278 0001563  84.6643 275.4712 14.19552572 30449
# """

tle = """
TERRA                   
1 25994U 99068A   23172.51277846  .00000597  00000+0  13601-3 0  9990
2 25994  98.0941 240.7913 0002831  75.1003 339.3190 14.59263023250413
"""

lines = tle.strip().splitlines()

satellite = EarthSatellite(lines[1], lines[2], lines[0])
print(satellite)

ts = load.timescale()

targetLoc = wgs84.latlon(65, -24)
t_start = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc)
t_end  = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(hours=PARAMETERS['SCENARIO_LENGTH'])

# finding time, position, velocity of rise/culmination/set events
t, events = satellite.find_events(targetLoc, ts.from_datetime(t_start), ts.from_datetime(t_end), altitude_degrees=1.0)
eventZip = list(zip(t,events))
df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
# removing rise/set events
culmTimes = df.loc[df["Event"]==1]
# finding time of first culmination
culmTime = culmTimes.iloc[0]["Time"]
print("Culmination time 1 is",culmTime.utc)
# finding satellite position and velocity at first culmination time
culmGeocentric = satellite.at(culmTime)
# culmPos = culmGeocentric.position.m
# targetLoc2 = targetLoc.at(culmTime)

pos_vel= culmGeocentric.frame_xyz_and_velocity(itrs)
culm_pos = pos_vel[0].m
culm_vel = pos_vel[1].m_per_s
targetPos = targetLoc.itrs_xyz.m


sat_geographical = wgs84.geographic_position_of(culmGeocentric)
print("target",targetLoc)
print("satGEO",sat_geographical)
difference =  sat_geographical.longitude.degrees - targetLoc.longitude.degrees
print("DIFFFF",difference)

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

# Convert the rotation matrix to a quaternion
iQuat = R.from_matrix(R_bi).as_quat()

print("iQuat", iQuat[0], ",", iQuat[1], ",", iQuat[2], ",", iQuat[3])

# find roll angle between nadir vector and target
culmUnitVec = culm_pos/np.linalg.norm(culm_pos)
targetUnitVec = targetPos/np.linalg.norm(targetPos)

direction =   culm_pos - targetPos
dirUnit = direction/np.linalg.norm(direction)

rollAngle = np.arccos(np.dot(dirUnit, culmUnitVec)) 

# rollAngle is always positive - need to fix when target is to right
if culm_vel[2] > 0 and sat_geographical.longitude.degrees < targetLoc.longitude.degrees:
    rollAngle = -rollAngle
    
if culm_vel[2] < 0 and sat_geographical.longitude.degrees > targetLoc.longitude.degrees:
    rollAngle = -rollAngle


targetRot = R.from_matrix(R_bi)*R.from_euler('x',rollAngle)
rollAngledeg = np.rad2deg(rollAngle)
targetQuat = targetRot.as_quat()

x0 = iQuat[0]
y0 = iQuat[1]
z0 = iQuat[2]
w0 = iQuat[3]

x1 = targetQuat[0]
y1 = targetQuat[1]
z1 = targetQuat[2]
w1 = targetQuat[3]

xn = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
yn = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
zn = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1
wn = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1

rollQuat = np.array([xn, yn, zn, wn])

qT = np.array(
    [
        [targetQuat[3], targetQuat[2], -targetQuat[1], -targetQuat[0]],
        [-targetQuat[2], targetQuat[3], targetQuat[0], -targetQuat[1]],
        [targetQuat[1], -targetQuat[0], targetQuat[3], -targetQuat[2]],
        [targetQuat[0], targetQuat[1], targetQuat[2], targetQuat[3]],
    ]
)

qB = np.array([iQuat[0], iQuat[1], iQuat[2], iQuat[3]])

errorQuat = np.matmul(qT, qB)
errorRot = R.from_quat(errorQuat)
errorAngle = np.rad2deg((R.magnitude(errorRot)))

# print("culmination time",culmTime.utc_iso())
print("Roll Angle", [rollAngledeg])
print("culmination position",[culm_pos])
print("targetQuat", targetQuat[0], ",", targetQuat[1], ",", targetQuat[2], ",", targetQuat[3])


                       

        

