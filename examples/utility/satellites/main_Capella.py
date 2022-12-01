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

from examples.utility.config import PARAMETERS

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

    # initialize the Constellation object class from TLEs    
    constellation = Constellation('capella', app, indices, names, field_of_regard, tles=TLES)

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
        time_status_init=PARAMETERS['SCENARIO_START'],
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
        # print(app.simulator.get_mode())