import os
import json
import string
import random
from datetime import datetime, timezone, timedelta
import numpy as np

import pandas as pd

PARAMETERS = pd.Series(
    data={
        # Global parameters
        "PREFIX": "BCtest",
        "SCALE": 100,
        "SCENARIO_START": datetime(2023, 1, 1, 7, 0, 0).timestamp(),
        "SCENARIO_LENGTH": 10000,

        # Name of satellite for reference orbit from Celestrak database SUOMI NPP, GOES 18, NAVSTAR 72 (USA 258)
        "name": "SUOMI NPP",

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

        # ADCS system parameters
        # Controller gains
        "Kp": 0.01,
        "Ki": 0.01,
        "Kd": 0.0001,
        
        # Define initial state of satellite
        "cubeMass": 2,                                                            # mass of single cubesat cube (kg)
        "cubeLength": 0.1,                                                        # length of single cubesat cube (m)
  
        
        # Actuators
        "rxnwl_mass": 226e-3,
        "rxnwl_radius": 0.5 * 65e-3,
        "rxnwl_max_torque": np.inf,
        "rxnwl_max_momentum": np.inf,
        "noise_factor": 0.0,

        # Satellite parameters
        "TLES": {},

        # Manager Parameters:
        "UPDATE": []
    }
)