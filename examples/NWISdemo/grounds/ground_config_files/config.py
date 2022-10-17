import os
import pandas as pd

PREFIX = os.getenv("PREFIX", "BCtest")
NAME = os.getenv("NAME", "Grounds")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Broadcasts it\'s location to the testbed on the "{PREFIX}/ground/location" topic.',
}
HOST, PORT = "testbed.mysmce.com", 8883
USERNAME, PASSWORD = "bchell", "cT8T1pd62KnZ"

# Default location is Svalbard Satellite Station
LAT = float(os.getenv("LAT", 78.229772))
LNG = float(os.getenv("LNG", 15.407786))
MIN_ELEVATION = 5.0  # minimum view angle (degrees) for ground-satellite communications
SCALE = 60

GROUND = pd.DataFrame(
    data={
        "groundId": [0],
        "latitude": [LAT],
        "longitude": [LNG],
        "elevAngle": [MIN_ELEVATION],
        "operational": [True],
    }
)
