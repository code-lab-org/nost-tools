import os
# from skyfield.api import load
# for walker delta TLE's
from constellation_tle import generate_walker_delta_members
# import orekit
import pandas as pd


PREFIX = os.getenv("PREFIX", "BCtest")
NAME = "constellation"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Satellites broadcast location on BCtest/satellite/location, image taken and image downlinked events on BCtest/constellation/imageTaken and BCtest/constellation/imageDownlinked. Subscribes to BCtest/streamGauge/floodWarning.",
}

FIELD_OF_REGARD = float(
    os.getenv("FIELD_OF_REGARD", 112) # 22.5 half angle?
)
MIN_ELEVATION_COMMS = float(
    os.getenv("MIN_ELEVATION_COMMS", 5.0)
)

SCALE = 60

# Generate satellite names and TLE's for Walker-Delta constellation
# Sentinel 2A
WDconstellation= {
        "name": "FloodImager",
        "lead_orbit": {
          "type": "tle",
          "tle": [
            "1 40697U 15028A   22056.51523779  .00000065  00000+0  41387-4 0  9993",
            "2 40697  98.5707 132.8745 0001194  86.6068 273.5250 14.30814867348846"
          ]
        },
        "number_satellites": 10,
        "number_planes": 10,
        "relative_spacing": 0
      }

a = generate_walker_delta_members(WDconstellation)
condf=pd.DataFrame(columns=["name","tle1","tle2"])
TLES = []
for i in range(len(a)):
    condf= condf.append({"name":a[i]["name"], "tle1": a[i]["orbit"][0], "tle2": a[i]["orbit"][1]},ignore_index=True)
    names = list(condf["name"])
    TLES.append(list([condf["tle1"][i], condf["tle2"][i]]))
