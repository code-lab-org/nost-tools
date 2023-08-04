import os

PREFIX = os.getenv("PREFIX", "liveDemo")
NAME = os.getenv("NAME", "dashboard")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Dashboard monitoring the "{PREFIX}/#" topic.',
}
SCALE = 60.0
