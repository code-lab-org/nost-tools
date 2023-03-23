"""
    *This application demonstrates a manager synchronizing a test case between disaggregated applications*
    
    This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :obj:`ManagedApplication` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.
"""

import logging
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values
from skyfield.api import utc

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.manager import Manager

from config import PARAMETERS

logging.basicConfig(level=logging.INFO)


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]
    CA_LIST = credentials["CA_LIST"]
    CERTIFICATE = credentials["CERTIFICATE"]
    KEY = credentials["KEY"]
    
    # set the client credentials from the config file
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, CA_LIST, CERTIFICATE, KEY, True)

    # create the manager application from the template in the tools library
    manager = Manager()

    # add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # start up the manager on PREFIX from config file
    manager.start_up(PARAMETERS['PREFIX'], config, True)

    # execute a test plan
    manager.execute_test_plan(
        datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc),                                         # scenario start datetime
        datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(hours=PARAMETERS['SCENARIO_LENGTH']),                                           # scenario end datetime
        start_time=None,                                        # optionally specify a wallclock start datetime for synchronization
        time_step=timedelta(seconds=1),                         # wallclock time resolution for simulation
        time_scale_factor=PARAMETERS['SCALE'],                                # initial scale between wallclock and scenario clock (e.g. if SCALE = 60.0 then  1 wallclock second = 1 scenario minute)
        time_scale_updates=PARAMETERS['UPDATE'],                              # optionally schedule changes to the time_scale_factor at a specified scenario time
        time_status_step=timedelta(seconds=5) * PARAMETERS['SCALE'],                                                # optional duration between time status 'heartbeat' messages
        time_status_init=datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(minutes=1),                                                      # optional initial scenario datetime to start publishing time status 'heartbeat' messages
        command_lead=timedelta(seconds=5),                                                      # lead time before a scheduled update or stop command
    )