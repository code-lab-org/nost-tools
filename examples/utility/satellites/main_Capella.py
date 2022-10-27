# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of satellites for monitoring events propagated from Two-Line Elements (TLEs)*
    
    The application contains one :obj:`Constellation` (:obj:`Entity`) object class, one :obj:`PositionPublisher` (:obj:`WallclockTimeIntervalPublisher`), and two :obj:`Observer` object classes to monitor for :obj:`EventDetected` and :obj:`EventReported` events, respectively. The application also contains several methods outside of these classes, which contain standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson.

"""

import time
import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

from skyfield.api import load
from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from constellation import *

from examples.utility.satellites.satellite_config_files.capella_config import (
    PREFIX,
    NAME,
    SCALE,
    TLES,
    FIELD_OF_REGARD,
)

logging.basicConfig(level=logging.INFO)


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]
    
    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication(NAME)

    # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    activesats = load.tle_file(activesats_url, reload=True)
    by_name = {sat.name: sat for sat in activesats}

    # Names of Capella satellites used in Celestrak database
    names = ["CAPELLA-1-DENALI", \
            "CAPELLA-2-SEQUOIA", \
            "CAPELLA-3-WHITNEY", \
            "CAPELLA-4-WHITNEY", \
            "CAPELLA-5-WHITNEY", \
            "CAPELLA-6-WHITNEY", \
            "CAPELLA-7-WHITNEY", \
            "CAPELLA-8-WHITNEY"]
    ES = []
    indices = []
    for name_i, name in enumerate(names):
        ES.append(by_name[name])
        indices.append(name_i)
    
    # initialize the Constellation object class (in this example from EarthSatellite type)
    constellation = Constellation('capella', app, indices, names, FIELD_OF_REGARD, ES)

    # add observer classes to the Constellation object class
    constellation.add_observer(EventDetectedObserver(app))
    constellation.add_observer(EventReportedObserver(app))

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(constellation)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(
        PositionPublisher(app, constellation, timedelta(seconds=2))
    )

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2022, 10, 3, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=2) * SCALE,
    )

    # add message callbacks
    app.add_message_callback("event", "location", constellation.on_event)
    app.add_message_callback("ground", "location", constellation.on_ground)

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(1)
