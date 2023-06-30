import os
import random
from datetime import datetime, timezone

PREFIX = os.getenv("PREFIX", "utility")
NAME = os.getenv("NAME", "randomGlobalEvents")
LOG = f"\x1b[1m[\x1b[31m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Publishes event location and four parameters that define the time-dependent utility curves for each event. Predicted values are published at the beginning of the simulation, while actual is reported in simulation time",
}

# Define faster-than-real-time scale for simulated scenario
SCALE = 3600.0 # NOTE: SCALE = 3600 means 1 second wallclock time = 1 hour scenario time

# Define number of random events and maximum possible duration for an event
EVENT_COUNT = 3
MAX_EVENT_DURATION = 36.00 # in hours, converted to timedelta within application

# Define range of time when random events can occur
SCENARIO_START = datetime(2023, 8, 2, 7, 20, tzinfo=timezone.utc)
SCENARIO_LENGTH = 144.00 # in hours, converted to timedelta within application

# User can hardcode a SEED for repeatable results, but template is for a random generator)
SEED = random.randint(0, 1000000000000)