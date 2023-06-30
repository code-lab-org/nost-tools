# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 11:43:17 2023

@author: mlevine4
"""

import logging
import sys, time, signal
import serial # type: ignore
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
import pandas as pd # type: ignore


from nost_tools.application_utils import ConnectionConfig, ShutDownObserver # type: ignore
from nost_tools.observer import Observer, Observable # type: ignore
from nost_tools.managed_application import ManagedApplication # type: ignore
from nost_tools.publisher import WallclockTimeIntervalPublisher # type: ignore

logging.basicConfig(level=logging.INFO)

################################################################
# Global script variables.

serial_port = None
client = None

################################################################
# Attach a handler to the keyboard interrupt (control-C).
def _sigint_handler(signal, frame):
    print("Keyboard interrupt caught, closing down...")
    if serial_port is not None:
        serial_port.close()

    if client is not None:
        client.loop_stop()
        
    sys.exit(0)

signal.signal(signal.SIGINT, _sigint_handler) 
       
################################################################

class StateMachine(Observable,Observer):
    """
    *The StateMachine object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        state (int): Integer value indicating current reported state of state machine (defaults to 0)
    """

    def __init__(self, app, initial_state = 0, initial_rotations = 0):
        super().__init__()
        self.app = app
        self.state = initial_state
        self.rotations = initial_rotations

# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], credentials["PORT"]
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("Arduino_serial")
    
    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))
    
    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        "serial",
        config,
        True,
        time_status_step=timedelta(seconds=10),
        time_status_init=datetime(2023, 5, 1, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1),
    )