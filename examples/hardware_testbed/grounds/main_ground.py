import time
import math
import numpy as np

from time import sleep
from datetime import datetime, timedelta
from dotenv import dotenv_values
from config import PREFIX
from skyfield.api import load, wgs84, Topos, utc
from math import radians, cos, sin, asin, sqrt, atan2, pi, log, log10
from scipy import constants
light = constants.speed_of_light

from ground_config_files.config import *
from ground_config_files.signal import lambda_uplink

def haversine(grndLNG, grndLAT, satLNG, satLAT):
    
    earthRad = 6371 # km
    
    # grnd = LAT/LNG1, sat = LAT/LNG2
    grndLNG_radians = radians(grndLNG) 
    grndLAT_radians = radians(grndLAT)
    satLNG_radians = radians(satLNG)
    satLAT_radians = radians(satLAT)
    
    deltLAT = satLAT_radians - grndLAT_radians
    deltLNG = satLNG_radians - grndLNG_radians
    
    a = sin(deltLAT/2)**2 + cos(grndLAT_radians)*cos(satLAT_radians) * (sin(deltLNG/2)**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    dist = earthRad * c
    return dist

def fspl_nondb(distance, frequency):
    result = ((4 * math.pi * (distance*1000) * (frequency*1000000))/(light))**2
    return result

def fspl_db(distance, frequency):
    wave = light / (frequency*1000000)
    result = 20*log10(distance*1000) + 20*log10(frequency*1000000) - 147.55
    return result

def signal_loss(pwr, fspldB):
    result = pwr - fspldB
    return result

eph = load('de421.bsp')
earth = eph['earth']
ts = load.timescale()
now = datetime.utcnow()
current_time = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)

sat_url = 'http://celestrak.org/NORAD/elements/stations.txt'
satellites = load.tle_file(sat_url, reload=True)
by_name = {sat.name: sat for sat in satellites}
satellite = by_name['ISS (ZARYA)']

issLAT, issLNG = wgs84.latlon_of(satellite.at(current_time))
issLATdeg = issLAT.degrees
issLNGdeg = issLNG.degrees

distance_from_grnd = haversine(LNG, LAT, issLNGdeg, issLATdeg)


fspl_non = fspl_nondb(distance_from_grnd, uplink)
fspl_dec = fspl_db(distance_from_grnd, uplink)
signal_loss_dBW = signal_loss(power, fspl_dec) 



# print(issLAT)
# print(issLNG)
print("Distance from ISS to ground station: " + "{:.2f}".format(distance_from_grnd) + " km")
print("FSPL (non-dB): " + np.format_float_scientific(fspl_non, 3) + " m^2")
print("FSPL (dB): " + np.format_float_scientific(fspl_dec, 3) + " dB")
print("Signal loss: " + "{:.2f}".format(signal_loss_dBW) + " dBW")
