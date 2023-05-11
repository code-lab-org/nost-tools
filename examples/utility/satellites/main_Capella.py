# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of Capella satellites for 
    monitoring events propagated from Two-Line Elements (TLEs)*
"""

import time
import logging
import json
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

from skyfield.api import load, utc
from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from constellation import *

from examples.utility.config import PARAMETERS

logging.basicConfig(level=logging.INFO)


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    CERTIFICATE, KEY = credentials["CERTIFICATE"], credentials["KEY"]

    # set the client credentials
    config = ConnectionConfig(HOST, PORT, CERTIFICATE, KEY)

    # create the managed application
    app = ManagedApplication("capella")

    # Names of Capella satellites used in Celestrak database
    # NOTE: This is currently not working, as it seems which of these Capella satellites are included in Celestrak's database is inconsistent.
    names = ["CAPELLA-1-DENALI", \
            "CAPELLA-2-SEQUOIA", \
            "CAPELLA-3-WHITNEY", \
            "CAPELLA-4-WHITNEY", \
            "CAPELLA-5-WHITNEY", \
            "CAPELLA-6-WHITNEY", \
            "CAPELLA-7-WHITNEY", \
            "CAPELLA-8-WHITNEY"]
    
    field_of_regard = [80.0 for _ in names]

    # Checks if the TLES parameter is given and if not pulls the most recent ones from Celestrak
    if PARAMETERS['TLES'] == {}:
        # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
        load.download("https://celestrak.com/NORAD/elements/active.txt")
        TLES = pd.Series(
            data=[[] for _ in names],
            index=names
        )
        with open("active.txt", "r") as f:
            f = list(f)
            for i, row in enumerate(f):
                if i % 3 == 0 and row.strip(' \n') in names:
                    TLES[row.strip(' \n')].append(f[i+1])
                    TLES[row.strip(' \n')].append(f[i+2])

    else: 
        TLES = pd.Series(json.loads(PARAMETERS["TLES"]["capella"]))

    
    print(TLES)
    # initialize the Constellation object class from TLEs    
    constellation = Constellation('capella', app, field_of_regard, tles=TLES)

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
        PARAMETERS['PREFIX'],
        config,
        True,
        time_status_step=timedelta(seconds=10) * PARAMETERS['SCALE'],
        time_status_init=datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=timezone.utc),
        time_step=timedelta(seconds=2) * PARAMETERS['SCALE'],
    )

    # add message callbacks
    app.add_message_callback("ground", "location", constellation.on_ground)
    app.add_message_callback("event", "start", constellation.on_event_start)
    app.add_message_callback("event", "dayChange", constellation.on_event_day_change)
    app.add_message_callback("event", "finish", constellation.on_event_finish)
    app.add_message_callback("manager", "init", constellation.on_manager_init)

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(0.2)