import os

PREFIX = os.getenv("PREFIX", "greenfield")
NAME = "delay"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Collects message timestamps and sizes to enable stress tests on the testbed",
}

# APPS = ["constellation", "fire", "ground", "manager"]
APPS = ["heartbeat"]

