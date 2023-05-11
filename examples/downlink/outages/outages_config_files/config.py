import os
import pandas as pd

PREFIX = os.getenv("PREFIX", "downlink")
NAME = "outage"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Scheduler of outages for ground stations",
}

SCALE = 60							
