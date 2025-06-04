import os

PREFIX = os.getenv("PREFIX", "greenfield")
NAME = os.getenv("NAME", "heartbeat")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f"Broadcasts periodic time status update to {PREFIX}/status/{NAME}/time",
}

SCALE = 1.0
MSG_LENGTH = 252399
# MSG_PERIOD = 7.994690033
MSG_PERIOD = 1.0  # seconds, rounded to nearest second for simplicity
