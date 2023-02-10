import time
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

from skyfield.api import utc
from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from config import PARAMETERS
from satellite import *

logging.basicConfig(level=logging.INFO)


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":

    # keycloak_openid = KeycloakOpenID("http://localhost:7777/auth/",
    #                                 client_id="solace",
    #                                 realm_name="Master",
    #                                 )

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("satellite")

    # Names of Capella satellites used in Celestrak database
    name = "SUOMI NPP"

    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    activesats = load.tle_file(activesats_url, reload=False)
    by_name = {sat.name: sat for sat in activesats}

    field_of_regard = 112.56

    satellite = Satellite(app, 0, 'satellite', field_of_regard, PARAMETERS['GROUND'], ES=by_name[name])

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(satellite)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(
        StatusPublisher(app, satellite, timedelta(seconds=5)*PARAMETERS['SCALE'])
    )

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PARAMETERS["PREFIX"],
        config,
        True,
        time_status_step=timedelta(seconds=5)*PARAMETERS['SCALE'],
        time_status_init=datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc),
        time_step=timedelta(seconds=1) * PARAMETERS['SCALE'],
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(0.2)
