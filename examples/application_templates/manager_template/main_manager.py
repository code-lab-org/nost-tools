# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.manager import Manager

# The test suite event prefix, time scale, and any updated time scales go in the config.py file
from manager_config_files.config import (
    PREFIX,
    SCALE,
    UPDATE,
)

logging.basicConfig(level=logging.INFO)

# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials from the config file
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the manager application from the template in the tools library
    manager = Manager()

    # add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # start up the manager on PREFIX from config file
    manager.start_up(PREFIX, config, True)

    # execute a test plan
    manager.execute_test_plan(
        datetime(2020, 1, 1, 7, 20, 0, tzinfo=timezone.utc),  # scenario start datetime
        datetime(2020, 1, 1, 10, 20, 0, tzinfo=timezone.utc),  # scenario stop datetime
        start_time=None,  # optionally specify a wallclock start datetime for synchronization
        time_step=timedelta(seconds=1),  # wallclock time resolution for simulation
        time_scale_factor=SCALE,  # initial scale between wallclock and scenario clock (e.g. if SCALE = 60.0 then  1 wallclock second = 1 scenario minute)
        time_scale_updates=UPDATE,  # optionally schedule changes to the time_scale_factor at a specified scenario time
        time_status_step=timedelta(seconds=1)
        * SCALE,  # optional duration between time status 'heartbeat' messages
        time_status_init=datetime(
            2020, 1, 1, 7, 21, 0, tzinfo=timezone.utc
        ),  # optional initial scenario datetime to start publishing time status 'heartbeat' messages
        command_lead=timedelta(
            seconds=2
        ),  # lead time before a scheduled update or stop command
    )
