import os

PREFIX = os.getenv("PREFIX", "BCtest")
NAME = "satellite"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Satellites broadcast location on downlink/constellation/location, and detect and report events on downlink/constellation/detected and downlink/constellation/reported. Subscribes to downlink/fire/location.",
}

Kp = 0.1         # controller proportional gain
Ki = 0.1         # controller integral gain
Kd = 0.1         # controller derivative gain
