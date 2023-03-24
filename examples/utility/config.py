import os
import json
import string
import random
from datetime import datetime, timezone, timedelta

import pandas as pd

# Name of next simulation run
sim_name = 'test'

# Name of simulation file to pull parameters from. if None, use below parameters
param_file = None

if param_file == None:
    seed = random.randint(0, 1000000000000)

    PARAMETERS = pd.Series(
        data={
            # Global parameters
            "PREFIX": "utility",
            "SCALE": 60,
            "SCENARIO_START": datetime(2022, 11, 1, 7, 0, 0, tzinfo=timezone.utc).timestamp(),
            "SCENARIO_LENGTH": 1,
            "SIM_NAME": sim_name,

            # Event parameters
            "SEED": seed,
            # "SEED": "123testdaynightseed",
            "EVENT_COUNT": 50,
            "EVENT_LENGTH": 2,
            "EVENT_START_RANGE": (-1, 1),

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
   
else:
    # Read parameters from sim output file
    with open(f"outputs/{param_file}.json") as json_data:
        PARAMETERS = json.load(json_data)

    PARAMETERS = pd.Series(PARAMETERS)
    PARAMETERS["SIM_NAME"] = sim_name

    # DataFrame object gets lost when written to file, need to rebuild it
    PARAMETERS["GROUND"] = pd.DataFrame(PARAMETERS["GROUND"]).transpose()