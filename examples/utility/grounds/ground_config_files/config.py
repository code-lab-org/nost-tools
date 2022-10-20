import os
import pandas as pd

PREFIX = os.getenv("PREFIX", "utility")
NAME = os.getenv("NAME", "Grounds")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Broadcasts it\'s location to the testbed on the "{PREFIX}/ground/location" topic.',
}

# Default location is Svalbard, Norway
LAT = float(os.getenv("LAT", 78.229772))
LNG = float(os.getenv("LNG", 15.407786))
MIN_ELEVATION = 5.0  # minimum view angle (degrees) for ground-satellite communications
SCALE = 20

# define grounds in a Dataframe constructed from a Python dictionary
GROUND = pd.DataFrame(
    # data={
    #     "groundId": [0, 1, 2, 3, 4, 5, 6],
    #     "latitude": [35.0, 30.0, -5.0, -30.0, 52.0, -20.0, 75.0],
    #     "longitude": [-102.0, -9.0, -60.0, 25.0, 65.0, 140.0, -40.0],
    #     "elevAngle": [5.0, 15.0, 5.0, 10.0, 5.0, 25.0, 15.0],
    #     "operational": [True, True, True, True, True, False, False],
    # }
    data={
        "groundId": [0],
        "latitude": [LAT],
        "longitude": [LNG],
        "elevAngle": [MIN_ELEVATION],
        "operational": [True],
    }
)
