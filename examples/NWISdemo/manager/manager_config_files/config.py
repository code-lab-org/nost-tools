import os
from datetime import datetime, timezone
from nost_tools.manager import TimeScaleUpdate

PREFIX = os.getenv("PREFIX", "BCtest")
NAME = os.getenv("NAME", "Manager")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Synchronizes a test case on the testbed on the "{PREFIX}/#" topic.',
}
HOST, PORT = "testbed.mysmce.com", 8883
USERNAME, PASSWORD = "bchell", "cT8T1pd62KnZ"
SCALE = 60
UPDATE = [
    # TimeScaleUpdate(120.0, datetime(2020, 1, 1, 9, 40, 0, tzinfo=timezone.utc)),
    # TimeScaleUpdate(300.0, datetime(2020, 1, 1, 20, 20, 0, tzinfo=timezone.utc)),
]
