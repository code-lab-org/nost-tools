# -*- coding: utf-8 -*-
"""
Created on Wed May 31 15:55:14 2023

@author: brian
"""

from skyfield.api import EarthSatellite, load, wgs84
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R

culm = []

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

# for i in range(culmTimes):
#     df["culmPosX"] = satellite.at(culmTimes)(culmTimes.iloc[0]["Time"]).position.m[0]

culmTime = (culmTimes.iloc[0]["Time"]).utc_iso()
culmPos = satellite.at(culmTimes.iloc[0]["Time"]).position.m
targetPos = hoboken.at(culmTimes.iloc[0]["Time"]).position.m

culmUnitVec = culmPos/np.linalg.norm(culmPos)
targetUnitVec = targetPos/np.linalg.norm(targetPos)

angle = np.arccos(np.dot(culmUnitVec, targetUnitVec))

r = R.from_euler('x',angle)
targetQuat = r.as_quat()

                       