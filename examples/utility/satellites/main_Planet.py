# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of Planet satellites for monitoring events propagated from Two-Line Elements (TLEs)*
"""
import os
import sys
import time
import logging
import json
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from constellation import *

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
superparent = os.path.dirname(parent)

sys.path.append(superparent)
sys.path.append(parent)

from config import PARAMETERS

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
    app = ManagedApplication("planet")
    
    # Names of Planet satellites used in Celestrak database
    names = ["SKYSAT-A", \
                "SKYSAT-B", \
                "SKYSAT-C1", \
                "SKYSAT-C2", \
                "SKYSAT-C3", \
                "SKYSAT-C4", \
                "SKYSAT-C5", \
                "SKYSAT-C6", \
                "SKYSAT-C7", \
                "SKYSAT-C8", \
                "SKYSAT-C9", \
                "SKYSAT-C10", \
                "SKYSAT-C11", \
                "SKYSAT-C12", \
                "SKYSAT-C13", \
                "SKYSAT-C14", \
                "SKYSAT-C15", \
                "SKYSAT-C16", \
                "SKYSAT-C17", \
                "SKYSAT-C18", \
                "SKYSAT-C19"]

    # Gives each satellite a field of regard of 50.0 degrees
    field_of_regard = [50.0 for _ in names]

    # Checks if the TLES parameter is given and if not pulls the most recent ones from Celestrak
    if PARAMETERS['TLES'] == {}:
        # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
        # load.download("https://celestrak.com/NORAD/elements/active.txt")
        TLES = pd.Series(
            data=[[] for _ in range(len(names))],
            index=names
        )
        with open("active.txt", "r") as f:
            f = list(f)
            for i, row in enumerate(f):
                if i%3 == 0 and row.strip(' \n') in names:
                    TLES[row.strip(" \n")].append(f[i+1])
                    TLES[row.strip(" \n")].append(f[i+2])
    else:
        TLES = pd.Series(json.loads(PARAMETERS["TLES"]["planet"]))

    # initialize the Constellation object class (in this example from EarthSatellite type)
    constellation = Constellation('planet', app, field_of_regard, night_sight=False, tles=TLES)

    # add observer classes to the Constellation object class
    constellation.add_observer(EventDetectedObserver(app))
    constellation.add_observer(EventReportedObserver(app))

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(constellation)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(
        PositionPublisher(app, constellation, timedelta(seconds=1))
    )

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PARAMETERS['PREFIX'],
        config,
        True,
        time_status_step=timedelta(seconds=10) * PARAMETERS['SCALE'],
        time_status_init=datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * PARAMETERS['SCALE'],
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