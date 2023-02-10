# -*- coding: utf-8 -*-
"""
Created on Thu May 13 17:06:13 2021

@author: Josue Tapia 
"""
import orekit
import math
from datetime import datetime, timedelta
vm = orekit.initVM()
import pandas as pd
from orekit.pyhelpers import setup_orekit_curdir
from pkg_resources import resource_stream
setup_orekit_curdir()

from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.bodies import CelestialBodyFactory
from org.orekit.frames import FramesFactory
from org.orekit.utils import Constants, PVCoordinatesProvider
from org.orekit.propagation.analytical.tle import TLE
from orekit.pyhelpers import datetime_to_absolutedate


class Satellite(object):
    """Represents a satellite in orbit.
    
    Attributes:
        name (str): unique name of this satellite.
        tle (list(str)): two-line elements.
        instruments (list(:obj:`Instrument`)): list of instruments.
    """
    def __init__(self, name, tle, instruments=[]):
        self.name = name
        self.tle = tle
        self.instruments = instruments

class Instrument(object):
    """Represents an instrument.
    
    Attributes:
        name (str): unique name of this instrument.
        field_of_regard (float): angular field (degrees) of valid observations.
        req_access_time (:obj:`timedelta`): minimum access time required for 
            valid observations.
        req_self_sunlit (:obj:`timedelta`, optional): True, if the satellite 
            must be sunlit for valid observations.
        req_target_sunlit (:obj:`timedelta`, optional): True, if the target 
            ground point must be sunlit for valid observations.
    """
    def __init__(self, name, field_of_regard=180, req_access_time=timedelta(0), 
                 req_self_sunlit=None, req_target_sunlit=None):
        self.name = name
        self.field_of_regard = field_of_regard
        self.req_access_time = req_access_time
        self.req_self_sunlit = req_self_sunlit
        self.req_target_sunlit = req_target_sunlit

def generate_walker_delta_members(WDconstellation):
    satellites = []
    for satellite in range(WDconstellation["number_satellites"]):
        satellites_per_plane = math.ceil(WDconstellation["number_satellites"]/WDconstellation["number_planes"])
        plane = satellite // satellites_per_plane
        num_planes = WDconstellation["number_planes"]
        rel_spacing = WDconstellation["relative_spacing"]
        lead_orbit = WDconstellation["lead_orbit"]
        lead_tle = TLE(lead_orbit["tle"][0], lead_orbit["tle"][1])
        tle = TLE(
            0, # satellite number
            'U', # classification
            0, # launch year
            0, # launch number
            'A  ', # launch piece
            0, # ephemeris type
            0, # element number
            lead_tle.getDate(), # epoch
            lead_tle.getMeanMotion(), # mean motion
            0.0, # mean motion first derivative
            0.0, # mean motion second derivative
            lead_tle.getE(), # eccentricity
            lead_tle.getI(), # inclination
            lead_tle.getPerigeeArgument(), # periapsis argument
            lead_tle.getRaan() + plane*2*math.pi/num_planes, # right ascension of ascending node
            # FIXME orekit constructor requires mean anomaly, rather than true anomaly (as specified for walker delta constellations)
            lead_tle.getMeanAnomaly() + ((satellite % satellites_per_plane)*num_planes
                         + rel_spacing*plane)*2*math.pi/(satellites_per_plane*num_planes), # mean anomaly
            0, # revolution number at epoch
            0.0 # b-star (ballistic coefficient)
        )
        satellites.append(
            {"name" : WDconstellation["name"] + "{:03d}".format(satellite+1),
            "orbit" : [
                tle.getLine1(),
                tle.getLine2()
            ]}
            
        )

    return satellites


# WDconstellation= {
#         "name": "FloodImager",
#         "lead_orbit": {
#           "type": "tle",
#           "tle": [
#             "1 40697U 15028A   22056.51523779  .00000065  00000+0  41387-4 0  9993",
#             "2 40697  98.5707 132.8745 0001194  86.6068 273.5250 14.30814867348846"
#           ]
#         },
#         "number_satellites": 3,
#         "number_planes": 3,
#         "relative_spacing": 0
#       }
# TLES =[]
# a = generate_walker_delta_members(WDconstellation)
# df=pd.DataFrame(columns=["name","tle1","tle2"])
# for i in range(len(a)):
#     df= df.append({"name":a[i]["name"], "tle1": a[i]["orbit"][0], "tle2": a[i]["orbit"][1]},ignore_index=True)
#     names = list(df["name"])
#     TLES=list([df["tle1"][i], df["tle2"][i]])
    #print(TLES)


# inst_Tesat=Instrument(
#     'Planet',
#     field_of_regard= 30,
#     req_access_time=timedelta(seconds=10)
#     )
# df=pd.DataFrame(columns=["name","tle1","tle2"])
# for i in range(len(a)):
#     df= df.append({"name":a[i]["name"], "tle1": a[i]["orbit"][0], "tle2": a[i]["orbit"][1]},ignore_index=True)
# satellites=[
#     Satellite(df['name'][i], tle=[df["tle1"][i], df["tle2"][i]],instruments=[inst_Tesat])
#     for i in range(len(df))
#     ]
# print("The satellites are", satellites)