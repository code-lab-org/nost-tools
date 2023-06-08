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

# Name(s) of satellite(s) used in Celestrak database
name = "SUOMI NPP"

activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
activesats = load.tle_file(activesats_url, reload=False)
by_name = {sat.name: sat for sat in activesats}

satellite=by_name[name]

ts = load.timescale()

hoboken = wgs84.latlon(40.7440, -64.0324)
t_start = ts.utc(2014, 1, 23)
t_length = timedelta(hours=24)
t_end = t_start + t_length


t, events = satellite.find_events(hoboken, t_start, t_end, altitude_degrees=0.0)
eventZip = list(zip(t,events))
df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
culmTimes = df.loc[df["Event"]==1]

# for i in range(culmTimes):
#     df["culmPosX"] = satellite.at(culmTimes)(culmTimes.iloc[0]["Time"]).position.m[0]


    

    
    

                       
