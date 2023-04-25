import os
import json
import string
import random
from datetime import datetime, timezone, timedelta

import pandas as pd

PARAMETERS = pd.Series(
    data={
        # Global parameters
        "PREFIX": "basic_template",
        "SCALE": 60,
        "SCENARIO_START": datetime(2023, 1, 1, 7, 0, 0).timestamp(),
        "SCENARIO_LENGTH": 1,

        # Satellite parameters
        "TLES": {},

        # Manager Parameters:
        "UPDATE": []
    }
)
