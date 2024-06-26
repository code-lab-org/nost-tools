import time
import logging
from datetime import datetime, timedelta
from dotenv import dotenv_values

from skyfield.api import utc, load
from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from satellite import Satellite, StatusPublisher
from satellite_config_files.config import PARAMETERS

logging.basicConfig(level=logging.INFO)


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("satellite")

    # Name(s) of satellite(s) used in Celestrak database
    name = "SUOMI NPP"

    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    activesats = load.tle_file(activesats_url, reload=False)
    by_name = {sat.name: sat for sat in activesats}

    satellite = Satellite(app, name, ES=by_name[name])

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(satellite)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(StatusPublisher(app, satellite, timedelta(seconds=1)))

    # start up the application on PREFIX, publish time status
    app.start_up(
        PARAMETERS["PREFIX"],
        config,
        True,
        time_status_step=timedelta(seconds=5) * PARAMETERS["SCALE"],
        time_status_init=datetime.fromtimestamp(PARAMETERS["SCENARIO_START"]).replace(
            tzinfo=utc
        ),
        time_step=timedelta(seconds=1) * PARAMETERS["SCALE"],
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(0.2)
