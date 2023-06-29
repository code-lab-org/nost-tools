import os
import random
from datetime import datetime, timezone, timedelta

PREFIX = os.getenv("PREFIX", "utility")
NAME = os.getenv("NAME", "Events")
LOG = f"\x1b[1m[\x1b[31m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Publishes event location and four parameters that define the time-dependent utility curves for each event. Predicted values are published at the beginning of the simulation, while actual is reported in simulation time",
}
SCALE = 3600.0
EVENT_COUNT = 3
ALPHA = [0.5, 7.5]
BETA = [0.5, 7.5]
DELAY = [-5, 5]
DURATION = [12, 72]
SCENARIO_START = datetime(2023, 8, 2, 7, 20, tzinfo=timezone.utc)
SCENARIO_LENGTH = 144
SEED = random.randint(0, 1000000000000)