# from asyncio.windows_events import NULL
import random
import os

PREFIX = os.getenv("PREFIX", "utility")
NAME = os.getenv("NAME", "Event")
LOG = f"\x1b[1m[\x1b[31m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Publishes historical fire data from the VIIRS instrument.",
}
SCALE = 60
SEED = 0
EVENT_COUNT = 500
EVENT_LENGTH = 12*60
EVENT_TIMESPAN = 12*60