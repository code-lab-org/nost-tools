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
        "SCALE": 60,
        "SCENARIO_START": datetime(2022, 11, 1, 7, 0, 0, tzinfo=timezone.utc).timestamp(),
        "SCENARIO_LENGTH": 1,

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