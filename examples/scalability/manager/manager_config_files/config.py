import os

PREFIX = os.getenv("PREFIX", "greenfield")
NAME = os.getenv("NAME", "Manager")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Synchronizes a test case on the testbed on the "{PREFIX}/#" topic.',
}

SCALE = 1.0
