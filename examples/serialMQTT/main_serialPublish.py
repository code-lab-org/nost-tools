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
from nost_tools.entity import Entity # type: ignore
from nost_tools.managed_application import ManagedApplication # type: ignore
from nost_tools.publisher import WallclockTimeIntervalPublisher # type: ignore

logging.basicConfig(level=logging.INFO)

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