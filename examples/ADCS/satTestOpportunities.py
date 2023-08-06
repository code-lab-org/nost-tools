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
targetList = [{"Latitude":1.5,"Longitude":-115}]
targetLoc = wgs84.latlon(-35,-8)

def new_target_location():
    new_lat = np.random.random()*180-90
    new_lon = np.random.random()*360-180
    new_targetList = {"Latitude":new_lat,"Longitude":new_lon}
    targetList.append(new_targetList)
    targetLoc = wgs84.latlon(new_lat,new_lon)
    return targetLoc


t_start = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc)
t_end  = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(hours=PARAMETERS['SCENARIO_LENGTH'])

# finding time, position, velocity of rise/culmination/set events
t, events = satellite.find_events(targetLoc, ts.from_datetime(t_start), ts.from_datetime(t_end), altitude_degrees=5.0)
event_times = t.utc_datetime()
eventZip = list(zip(event_times,events))
df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
# removing rise/set events
culmTimes = df.loc[df["Event"]==1]

# finding time of next opportunity
next_opportunities_df = culmTimes.loc[culmTimes.Time > datetime.now(tz=utc)].copy()

if next_opportunities_df.empty:
    targetLoc = new_target_location()  # doesn't go back to 57 function will work

# dropping past culmination times
next_opportunity_time = next_opportunities_df.iloc[0]["Time"]

# finding satellite position and velocity at next culmination time
culmGeocentric = satellite.at(ts.from_datetime(next_opportunity_time))
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

direction = culm_pos - targetPos
dirUnit = direction/np.linalg.norm(direction)

rollAngle = np.arccos(np.dot(dirUnit, culmUnitVec)) 

# making roll in correct direction
if culm_vel[2] > 0 and sat_geographical.longitude.degrees < targetLoc.longitude.degrees:
    rollAngle = -rollAngle
    
if culm_vel[2] < 0 and sat_geographical.longitude.degrees > targetLoc.longitude.degrees:
    rollAngle = -rollAngle


targetRot = R.from_matrix(R_bi)*R.from_euler('x',rollAngle)
rollAngledeg = np.rad2deg(rollAngle)
targetQuat = targetRot.as_quat()

# print("culmination time",culmTime.utc_iso())
print("Roll Angle", [rollAngledeg])
print("culmination position",[culm_pos])
print("targetQuat", targetQuat[0], ",", targetQuat[1], ",", targetQuat[2], ",", targetQuat[3])


                       

        

