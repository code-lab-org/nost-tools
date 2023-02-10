# -*- coding: utf-8 -*-
"""
    *This application demonstrates a manager synchronizing a test case between disaggregated applications*
    
    This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :obj:`ManagedApplication` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.
    
    .. literalinclude:: /../../manager/main_manager.py
    	:lines: 12-
    
"""

import logging
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values
import json

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.manager import Manager

# client credentials should be saved to config.py file in manager_config_files directory
from manager_config_files.config import PREFIX, SCALE

logging.basicConfig(level=logging.INFO)

# Note that these are loaded from a .env file in current working directory
credentials = dotenv_values(".env")
HOST, PORT = credentials["HOST"], int(credentials["PORT"])
USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

def on_ready(client, userdata, message):
    print("Manager received Ready status message from heartbeat application")
    
def on_mode(client, userdata, message):
    data = json.loads(message.payload.decode("utf-8"))
    print(data["properties"]["mode"])

# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # set the client credentials from the config file
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the manager application from the template in the tools library
    manager = Manager()

    # add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # start up the manager on PREFIX from config file
    manager.start_up(PREFIX, config, True)

    # subscribe specifically to the heartbeat/ready topic    
    manager.client.subscribe(("f{PREFIX}/status/heartbeat/ready",0))
    manager.client.subscribe(("f{PREFIX}/status/heartbeat/mode",0))
    
    # add message callbacks
    manager.add_message_callback("status/hearbeat", "ready", on_ready)
    manager.add_message_callback("status/heartbeat", "mode", on_mode)
    
    
    # execute a test plan
    manager.execute_test_plan(
        datetime(2021, 12, 13, 0, 0, 0, tzinfo=timezone.utc),                   # scenario start datetime
        datetime(2021, 12, 13, 0, 1, 0, tzinfo=timezone.utc),                   # scenario stop datetime
        start_time=None,                                                        # optionally specify a wallclock start time for synchronization
        time_step=timedelta(seconds=1),                                         # wallclock time resolution for simulation
        time_scale_factor=SCALE,                                                # scale between wallclock and scenario clock (in this case 1 wallclock second = 1 scenario minute)
        time_scale_updates=[],                                                  # optionally schedule changes to the time_scale_factor at a specified scenario time
        time_status_step=timedelta(seconds=12000000000000)* SCALE,              # optional frequency of time status 'heartbeat' messages
        time_status_init=datetime(2021, 12, 14, 2, 0, tzinfo=timezone.utc),     # optional initial scenario time to start publishing time status 'heartbeat' messages
        command_lead=timedelta(seconds=1),                                      # lead time before a scheduled update or stop command
    )