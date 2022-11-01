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

from examples.utility.config import (
    PREFIX,
    SCALE,
    SCENARIO_START,
    FIELD_OF_REGARD,
    TLES
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
    app = ManagedApplication("capella")

    # URL of most recent satellite two line elements
    load.download("https://celestrak.com/NORAD/elements/active.txt")

    # Names of Capella satellites used in Celestrak database
    names = ["CAPELLA-1-DENALI", \
            "CAPELLA-2-SEQUOIA", \
            "CAPELLA-3-WHITNEY", \
            "CAPELLA-4-WHITNEY", \
            "CAPELLA-5-WHITNEY", \
            "CAPELLA-6-WHITNEY", \
            "CAPELLA-7-WHITNEY", \
            "CAPELLA-8-WHITNEY"]
    
    indices = [i for i in range(len(names))]
    
    # Checks if the TLES parameter is given and if not pulls the most recent ones from Celestrak
    if TLES == None:
        # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
        load.download("https://celestrak.com/NORAD/elements/active.txt")
        TLES = {}
        with open("active.txt", "r") as f:
            for i, row in enumerate(f):
                if i%3 == 1 and row in names:
                    TLES[row] == [f[i+1], f[i+2]]

    
    # initialize the Constellation object class from TLEs    
    constellation = Constellation('capella', app, indices, names, FIELD_OF_REGARD["Capella"], tles=TLES)

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
        time_status_init=SCENARIO_START,
        time_step=timedelta(seconds=0.5) * SCALE,
    )

    # add message callbacks
    app.add_message_callback("event", "location", constellation.on_event)
    app.add_message_callback("ground", "location", constellation.on_ground)

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(1)