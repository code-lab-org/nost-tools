import os
import pandas as pd

PREFIX = os.getenv("PREFIX", "liveDemo")
NAME = os.getenv("NAME", "ground")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Broadcasts it\'s location to the testbed on the "{PREFIX}/ground/location" topic and tracks downlink duration, data offloaded, and link costs.',
}

DOWNLINK_RATE_AWS = 0.78156 # Gigabits/second
MIN_ELEVATION_AWS = 20.0  # minimum view angle (degrees) for ground-satellite communications
SCALE = 180.0

# define grounds in a Dataframe constructed from a Python dictionary
GROUND = pd.DataFrame(
    # Currently available AWS stations
    data={
        "groundId": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "latitude": [40.1625, 43.8041, 19.8968, -33.8688, 37.5665, 26.0667, -33.9249, 59.3293, 53.1424, -53.1638, 1.2840],
        "longitude": [-83.21, -120.5542, -155.5828, 151.2093, 126.978, 50.5577, 18.4241, 18.0686, -7.6921, -70.9171, 103.8488],
        "elevAngle": [MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS],
        "operational": [True, True, True, True, True, True, True, True, True, True, True],
        "downlinkRate": [DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS, DOWNLINK_RATE_AWS],
        "costPerSecond": [0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37],
        "costMode": ["discrete","discrete","discrete","discrete","discrete","discrete","discrete","discrete","discrete","discrete","discrete"],
    }
)
