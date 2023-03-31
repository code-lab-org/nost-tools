import os
from datetime import datetime, timezone
from nost_tools.manager import TimeScaleUpdate

PREFIX = os.getenv("PREFIX", "downlink")
NAME = os.getenv("NAME", "manager")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Synchronizes a test case on the testbed on the "{PREFIX}/#" topic.',
}

SCALE = 60.0
UPDATE = []
# UPDATE = [
#     TimeScaleUpdate(120.0, datetime(2020, 1, 1, 8, 20, 0, tzinfo=timezone.utc)),
#     TimeScaleUpdate(300.0, datetime(2020, 1, 1, 9, 20, 0, tzinfo=timezone.utc)),
# ]
