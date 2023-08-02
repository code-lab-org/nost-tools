# -*- coding: utf-8 -*-
"""
    *This application demonstrates a manager synchronizing a test case between disaggregated applications*
    
    This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :obj:`ManagedApplication` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.
"""
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values
from skyfield.api import utc # type:ignore

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver # type:ignore
from nost_tools.manager import Manager # type:ignore

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
# parent = os.path.dirname(current)
# superparent = os.path.dirname(parent)

# sys.path.append(superparent)
# sys.path.append(parent)

# client credentials should be saved to config.py file in manager_config_files directory
from manager_config_files.config import PREFIX, SCALE, SCENARIO_START, SCENARIO_LENGTH # type:ignore

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
        SCENARIO_START,                                         # scenario start datetime
        SCENARIO_START + timedelta(hours=SCENARIO_LENGTH),      # scenario end datetime
        start_time=None,                                        # optionally specify a wallclock start datetime for synchronization
        time_step=timedelta(seconds=1)*SCALE,                         # wallclock time resolution for simulation
        time_scale_factor=SCALE,                                # initial scale between wallclock and scenario clock (e.g. if SCALE = 60.0 then  1 wallclock second = 1 scenario minute)
        time_scale_updates=[],                              # optionally schedule changes to the time_scale_factor at a specified scenario time
        time_status_step=timedelta(seconds=1)*SCALE,                                                # optional duration between time status 'heartbeat' messages
        time_status_init=SCENARIO_START + timedelta(hours=1),                                                      # optional initial scenario datetime to start publishing time status 'heartbeat' messages
        command_lead=timedelta(seconds=5)                                                      # lead time before a scheduled update or stop command
    )