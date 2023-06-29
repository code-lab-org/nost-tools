import os
import pandas as pd

PREFIX = os.getenv("PREFIX", "template")
NAME = os.getenv("NAME", "Grounds")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Broadcasts its location to the testbed on the "{PREFIX}/ground/location" topic.',
}

# Default location is Svalbard, Norway
LAT = float(os.getenv("LAT", 78.229772))
LNG = float(os.getenv("LNG", 15.407786))
# minimum view angle (degrees) for ground-satellite communications
MIN_ELEVATION = 5.0
SCALE = 60.0

# define grounds in a Dataframe constructed from a Python dictionary
GROUND = pd.DataFrame(
    data={
        "groundId": [0],
        "latitude": [LAT],
        "longitude": [LNG],
        "elevAngle": [MIN_ELEVATION],
    }
    # data={
    #     "groundId": [0, 1, 2, 3, 4, 5, 6],
    #     "latitude": [35.0, 30.0, -5.0, -30.0, 52.0, -20.0, 75.0],
    #     "longitude": [-102.0, -9.0, -60.0, 25.0, 65.0, 140.0, -40.0],
    #     "elevAngle": [MIN_ELEVATION, 15.0, MIN_ELEVATION, 10.0, MIN_ELEVATION, 25.0, 15.0]
    # }
)
