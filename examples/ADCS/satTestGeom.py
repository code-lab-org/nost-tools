# -*- coding: utf-8 -*-
"""
Created on Wed May 31 15:55:14 2023

@author: brian
"""

from skyfield.api import EarthSatellite, load, wgs84, utc,  N, S, E, W
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



tle = """
SUOMI NPP
1 37849U 11061A   23159.44417251  .00000119  00000+0  77201-4 0  9999
2 37849  98.7042  98.3103 0000923  74.2604  58.9205 14.19566569601697
"""
lines = tle.strip().splitlines()

satellite = EarthSatellite(lines[1], lines[2], lines[0])



ts = load.timescale()

targetLoc = wgs84.latlon(-34.9055, -56.1851)
t_start = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc)
t_end  = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(hours=PARAMETERS['SCENARIO_LENGTH'])

# finding time, position, velocity of rise/culmination/set events
t, events = satellite.find_events(targetLoc, ts.from_datetime(t_start), ts.from_datetime(t_end), altitude_degrees=35.0)
eventZip = list(zip(t,events))
df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
# removing rise/set events
culmTimes = df.loc[df["Event"]==1]
# finding time of first culmination
culmTime = culmTimes.iloc[0]["Time"]
# finding satellite position and velocity at first culmination time
culmGeocentric = satellite.at(culmTime)
culmPos = culmGeocentric.position.m
targetPos = targetLoc.itrs_xyz.m
culmVel = culmGeocentric.velocity.m_per_s

sat_geographical = wgs84.geographic_position_of(culmGeocentric)
print(sat_geographical)

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

print(culmTime.utc_iso())
print("culmPos", [culmPos])
print("targetQuat", targetQuat[0], ",", targetQuat[1], ",", targetQuat[2], ",", targetQuat[3])

                       

        

