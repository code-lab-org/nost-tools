# -*- coding: utf-8 -*-
"""
    *This application demonstrates a network of ground stations given geospatial locations, minimum elevation angle constraints, and operational status*
    
    The application contains one class, the :obj:`Environment` class, which waits for a message from the manager that indicates the beginning of the simulation execution. The application publishes all of the ground station information once, at the beginning of the simulation.

"""

import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.simulator import Simulator, Mode
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication

from ground_config_files.schemas import SatelliteReady, SatelliteStatus, GroundLocation
from ground_config_files.config import (
    PREFIX,
    SCALE,
    GROUND,
)

logging.basicConfig(level=logging.INFO)

# define an observer to manage ground updates
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        grounds (:obj:`DataFrame`): DataFrame of ground station information including groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*)
    """

    def __init__(self, app, grounds):
        self.app = app
        self.grounds = grounds
        self.satelliteNames = []

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks when the **PROPERTY_MODE** switches to **EXECUTING** to send a :obj:`GroundLocation` message to the *PREFIX/ground/location* topic:
            
            .. literalinclude:: /../../firesat/grounds/main_ground.py
                :lines: 51-62

        """
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.EXECUTING:
            for index, ground in self.grounds.iterrows():
                self.app.send_message(
                    "location",
                    GroundLocation(
                        groundId=ground.groundId,
                        latitude=ground.latitude,
                        longitude=ground.longitude,
                        elevAngle=ground.elevAngle,
                        operational=ground.operational,
                        downlinkRate=ground.downlinkRate
                    ).json(),
                )
                
    def on_ready(self, client, userdata, message):
        ready = SatelliteReady.parse_raw(message.payload)
        self.satelliteNames.append(ready.name)
        
    def all_ready(self, client, userdata, message):
        self.groundTimes = {j:[] for j in self.satelliteNames}
        self.satView = {k:{"on":False,"linkCount":0} for k in self.satelliteNames}
         
    def on_commRange(self, client, userdata, message):
        satInView = SatelliteStatus.parse_raw(message.payload)
        if self.satView[satInView.name]["on"]:
            if not satInView.commRange:
                self.groundTimes[satInView.name][self.satView[satInView.name]["linkCount"]]["end"] = satInView.time
                self.satView[satInView.name]["on"] = False
                self.satView[satInView.name]["linkCount"] = self.satView[satInView.name]["linkCount"]+1
                
        elif satInView.commRange:
            self.groundTimes[satInView.name].append(
                {
                    "linkId":self.satView[satInView.name]["linkCount"],
                    "start":satInView.time,
                    "end":None,
                    "groundId":satInView.groundId
                },
            )
            self.satView[satInView.name]["on"] = True
        
def on_ready(client, userdata, message):
    """
    *Callback function appends a new satellite name in prep for all_ready method*

    .. literalinclude:: /../../firesat/grounds/main_ground.py
        :lines: 66-67

    """
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_ready(client, userdata, message)
            
def all_ready(client, userdata, message):
    """
    *Callback function creates two new dictionaries with keys corresponding to satellite names*

    .. literalinclude:: /../../firesat/grounds/main_ground.py
        :lines: 70-71

    """
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].all_ready(client, userdata, message)
            
def on_commRange(client, userdata, message):
    """
    *Callback function checks for transitions of commRange boolean*

    .. literalinclude:: /../../firesat/grounds/main_ground.py
        :lines: 74-89

    """
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_commRange(client, userdata, message)


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]
    
    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("ground")

    # add the environment observer to monitor simulation for switch to EXECUTING mode
    app.simulator.add_observer(Environment(app, GROUND))

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2020, 1, 1, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )
    
    # add message callbacks for fire ignition, detection, and report
    app.add_message_callback("constellation", "ready", on_ready)
    app.add_message_callback("constellation","allReady", all_ready)
    app.add_message_callback("constellation", "location", on_commRange)
