import os
import json
import string
import random
from datetime import datetime, timezone, timedelta

import pandas as pd

PARAMETERS = pd.Series(
    data={
        # Global parameters
        "PREFIX": "BCtest",
        "SCALE": 100,
        "SCENARIO_START": datetime(2023, 1, 1, 7, 0, 0).timestamp(),
        "SCENARIO_LENGTH": 10000,
        
        # Name of satellite for reference orbit from Celestrak database SUOMI NPP GOES 18
        "name": "NAVSTAR 72 (USA 258)",

        # satellite field of regard
        "field_of_regard": 112.56,

        # Ground parameters
        "GROUND": pd.DataFrame(
            data={
                "groundId": [0],
                "latitude": [78.229772],
                "longitude": [15.407786],
                "elevAngle": [5.0],
                "operational": [True],
            }
        ),

        # Satellite parameters
        "TLES": {},

        # Manager Parameters:
        "UPDATE": []
    }
)
