import os

PREFIX = os.getenv("PREFIX", "hawthorne")
NAME = os.getenv("NAME", "Hardware")
LOG = f"\x1b[1m[\x1b[32m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": f'Confirmation LED lights up upon message reception on  "{PREFIX}/constellation/detected" topic.',
}
TPC = f"{PREFIX}/constellation/detected"
