# -*- coding: utf-8 -*-

import os

PREFIX = os.getenv("PREFIX", "downlink")
NAME = "constellation"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Satellites broadcast location on downlink/constellation/location, and detect and report events on downlink/constellation/detected and downlink/constellation/reported. Subscribes to downlink/fire/location.",
}

TLE1_SC1 = str(os.getenv(
    "TLE1", "1 37849U 11061A   19365.87495 0.00000011  00000-0  25920-4	0  9999"))  # Historic SUOMI NPP TLE
TLE2_SC1 = str(os.getenv(
    "TLE2", "2 37849  98.7213 301.202 0001371  69.7366 357.989 14.19561536000000"))  # Historic SUOMI NPP TLE
TLE1_SC2 = str(os.getenv(
    "TLE1", "1 37849U 11061A   19365.87495 0.00000011  00000-0  25920-4	0  9999"))  # Historic SUOMI NPP TLE
TLE2_SC2 = str(os.getenv(
    "TLE2", "2 37849  53.7213 301.202 0001371  69.7366 357.989 14.19561536000000"))  # Historic SUOMI NPP TLE
TLES = [[TLE1_SC1,TLE2_SC1],[TLE1_SC2,TLE2_SC2]]

# FIELD_OF_REGARD = [#float(os.getenv("FIELD_OF_REGARD", 110)),
#     # float(os.getenv("FIELD_OF_REGARD", 110)),
#     float(os.getenv("FIELD_OF_REGARD", 112.56)),
#     float(os.getenv("FIELD_OF_REGARD", 112.56)),
#     # float(os.getenv("FIELD_OF_REGARD", 20.6)),
#     # float(os.getenv("FIELD_OF_REGARD", 20.6))
# ]  # degrees (found max zenith angle for MODIS is 65-degrees, FoR = 2 * zenith angle, field-of-view for VIIRS = 112.56-degrees)
# MIN_ELEVATION_COMMS = float(
#     os.getenv("MIN_ELEVATION_COMMS", 5.0)
# )  # degrees (comms more forgiving than sensor, not currently used)
# MIN_INTENSITY = float(os.getenv("MIN_INTENSITY", 10.0))  # square meters

SSR_CAPACITY = [280,343] # Capacity of onboard Solid State Recorder in Gigabits
CAPACITY_USED = [0.30, 0.25] # Fractional value from 0 (empty) to 1 (full). Arbitrarily starting with SSR half full, but will offload at first pass
INSTRUMENT_RATES = [.0125, .0125] # Rate of data collection for all instruments in Gigabits/second
COST_MODE = ["discrete","discrete"] # Options per satellite are "discrete" (per downlink), "continuous" (fixed contract), or "both"
FIXED_RATES = [0.09, 0.09] # Only used if "continuous" or "both" are the cost mode, otherwise costs reported by ground for "discrete"
SCALE = 60		