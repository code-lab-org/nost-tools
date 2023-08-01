import time
import logging
# import pandas as pd
from datetime import datetime, timedelta
from dotenv import dotenv_values

from skyfield.api import utc, EarthSatellite
from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from config import PARAMETERS
from satellite_with_multiple_targets_v_0 import Satellite, StatusPublisher

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
    # name = PARAMETERS["name"]

    # activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    # activesats = load.tle_file(activesats_url, reload=False)
    # by_name = {sat.name: sat for sat in activesats}
    
    # tle = """
    # NOAA 21 (JPSS-2)        
    # 1 54234U 22150A   23165.53076394  .00000086  00000+0  61482-4 0  9990
    # 2 54234  98.7165 103.5235 0001570  83.0372 277.0983 14.19552960 30675
    # """
    
    tle = """
TERRA                   
1 25994U 99068A   23172.51277846  .00000597  00000+0  13601-3 0  9990
2 25994  98.0941 240.7913 0002831  75.1003 339.3190 14.59263023250413
    """
    lines = tle.strip().splitlines()

    ES = EarthSatellite(lines[1], lines[2], lines[0])
    print(ES)

    field_of_regard = PARAMETERS["field_of_regard"]

    ADCSsat = Satellite(
        app, 0, "satellite", field_of_regard, PARAMETERS["GROUND"], tle)
    
    # print(satellite.ES)

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(ADCSsat)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(StatusPublisher(app, ADCSsat, timedelta(seconds=1)))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PARAMETERS["PREFIX"],
        config,
        True,
        time_status_step=timedelta(seconds=5) * PARAMETERS["SCALE"],
        time_status_init=datetime.fromtimestamp(PARAMETERS["SCENARIO_START"]).replace(
            tzinfo=utc
        ),
        time_step=timedelta(seconds=.1) * PARAMETERS["SCALE"],
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(0.2)
