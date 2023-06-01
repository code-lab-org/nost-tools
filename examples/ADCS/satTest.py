# -*- coding: utf-8 -*-
"""
Created on Wed May 31 15:55:14 2023

@author: brian
"""

from skyfield.api import EarthSatellite, load, wgs84
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R

# Name(s) of satellite(s) used in Celestrak database
name = "TERRA"

activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
activesats = load.tle_file(activesats_url, reload=False)
by_name = {sat.name: sat for sat in activesats}

satellite=by_name[name]

ts = load.timescale()

hoboken = wgs84.latlon(40.7440, -74.0324)
t0 = ts.utc(2014, 1, 23)
t1 = ts.utc(2014, 2, 30)

t, events = satellite.find_events(hoboken, t0, t1, altitude_degrees=15.0)
eventZip = list(zip(t,events))
df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
culmTimes = df.loc[df["Event"]==1]

geocentric = satellite.at(culmTimes.iloc[0]["Time"])

culmTime = (culmTimes.iloc[0]["Time"]).utc_iso()
culmPos = geocentric.position.m
targetPos = hoboken.at(culmTimes.iloc[0]["Time"]).position.m
culmVel = geocentric.velocity.m_per_s

h = np.cross(culmPos, culmVel)
# Calculate the unit vectors for the body x, y, and z axes
b_y = h / np.linalg.norm(h)
b_z = culmPos / np.linalg.norm(culmPos)
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
culmUnitVec = culmPos/np.linalg.norm(culmPos)
targetUnitVec = targetPos/np.linalg.norm(targetPos)

direction = culmPos - targetPos
dirUnit = direction/np.linalg.norm(direction)

rollAngle = np.arccos(np.dot(dirUnit, culmUnitVec))

targetRot = R.from_matrix(R_bi)*R.from_euler('x',rollAngle)
targetQuat = targetRot.as_quat()

print("targetQuat", targetQuat[0], ",", targetQuat[1], ",", targetQuat[2], ",", targetQuat[3])

                       

        

