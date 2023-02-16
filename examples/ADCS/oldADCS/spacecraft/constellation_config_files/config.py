import os
import numpy as np

PREFIX = os.getenv("PREFIX", "BCtest")
NAME = "Spacecraft1"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "",
}


SCALE = 60							
