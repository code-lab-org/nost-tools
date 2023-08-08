import os
import pandas as pd

PREFIX = os.getenv("PREFIX", "hawthorne")
NAME = os.getenv("NAME", "Grounds")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Broadcasts it\'s location to the testbed on the "{PREFIX}/ground/location" topic.',
}

power = 25 # Watts
uplink = 145.2 #MHz

LAT = 78.229772
LNG = 15.407786
MIN_ELEVATION = 5.0  # minimum view angle (degrees) for ground-satellite communications

GROUND = pd.DataFrame(
    data={
        "groundId": [0],
        "latitude": [LAT],
        "longitude": [LNG],
        "elevAngle": [MIN_ELEVATION],
        "operational": [True],
    }
)