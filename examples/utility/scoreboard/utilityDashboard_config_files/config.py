import os
from datetime import datetime, timezone

PREFIX = os.getenv("PREFIX", "utility")
NAME = os.getenv("NAME", "utilityDashboard")
LOG = f"\x1b[1m[\x1b[31m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "",
}
SCALE = 3600.0
EVENT_COUNT = 3
SCENARIO_START = datetime(2023, 8, 2, 7, 20, tzinfo=timezone.utc)
SCENARIO_LENGTH = 144