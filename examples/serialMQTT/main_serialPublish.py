# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 11:43:17 2023

@author: mlevine4
"""

import logging
import sys, time, signal
import serial
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
import pandas as pd


from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher

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
    app = ManagedApplication("Arduino_serial")