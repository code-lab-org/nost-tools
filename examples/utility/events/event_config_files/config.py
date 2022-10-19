import random
import os

PREFIX = os.getenv("PREFIX", "utility")
NAME = os.getenv("NAME", "Event")
LOG = f"\x1b[1m[\x1b[31m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Publishes historical fire data from the VIIRS instrument.",
}
SCALE = 60.0
EVENT_COUNT = 1000
