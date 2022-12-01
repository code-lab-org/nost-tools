import os
import csv
from datetime import datetime, timezone, timedelta

import pandas as pd

sim_name = "threeDayNightSightTest"
param_file = None

if param_file == None:
    
    PARAMETERS = pd.Series(
        data={
            # Global parameters
            "PREFIX": "utility",
            "SCALE": 60,
            "SCENARIO_START": datetime(2022, 11, 1, 7, 0, 0, tzinfo=timezone.utc),
            "SCENARIO_LENGTH": 3*24,
            "SIM_NAME": sim_name,

            # Event parameters
            "SEED": str(datetime.now()),
            # "SEED": "123testdaynightseed",
            "EVENT_COUNT": 50,
            "EVENT_LENGTH": 2*24,
            "EVENT_START_RANGE": (-1*24, 1*24),

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
    PARAMETERS = pd.read_csv(f"outputs/{param_file}.csv", on_bad_lines="skip", header=0, index_col=0).squeeze()
    # # PARAMETERS = pd.Series(str(f).split("\n\n\n")[0])
    # PARAMETERS["SIM_NAME"] = sim_name

    print(type(PARAMETERS["EVENT_START_RANGE"]))