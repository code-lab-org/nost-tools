import os
from datetime import datetime, timezone, timedelta

import pandas as pd

# Global parameters
PREFIX = os.getenv("PREFIX", "utility")
SCALE = 240
SCENARIO_START = datetime(2022, 10, 3, 7, 20, 0, tzinfo=timezone.utc)
SCENARIO_LENGTH = 12
SCENARIO_END = SCENARIO_START + timedelta(hours=SCENARIO_LENGTH)
SIM_NAME = "test_output"

# Event parameters
SEED = str(datetime.datetime.now())
EVENT_COUNT = 100
EVENT_LENGTH = 11
EVENT_START_RANGE = 1

# Ground parameters
GROUND = pd.DataFrame(
    data={
        "groundId": [0],
        "latitude": [float(os.getenv("LAT", 78.229772))],
        "longitude": [float(os.getenv("LNG", 15.407786))],
        "elevAngle": [5.0],
        "operational": [True],
    }
)

# Constellation parameters
FIELD_OF_REGARD = { 
    "Capella": 
        [float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0)),
        float(os.getenv("FIELD_OF_REGARD", 80.0))
    ], 
    "Planet": 
        [float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0)),
        float(os.getenv("FIELD_OF_REGARD", 50.0))
    ]
}
TLES = None

# Manager parameters
UPDATE = []