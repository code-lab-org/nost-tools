# -*- coding: utf-8 -*-
"""
    *This application demonstrates a simulation of a schedule of fires given geospatial locations and specified datetimes (at one minute resolution)*

    The application contains a single :obj:`Environment` class which listens to the time status published by the manager application and publishes fire information at the specified ignition :obj:`datetime`. The application also contains callback messages that updates :obj:`datetime` in the fires :obj:`DataFrame` for each of ignition (including latitude-longitude :obj:`GeographicPosition`), detection, and reporting.

"""

import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
import pandas as pd

pd.options.mode.chained_assignment = None

import importlib.resources

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication

from fire_config_files.schemas import FireState, FireStarted, FireDetected, FireReported
from fire_config_files.config import PREFIX, SCALE

logging.basicConfig(level=logging.INFO)

# define an observer to manage fire updates and record to a dataframe fires
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        fires (:obj:`DataFrame`): Dataframe of scenario scheduled fires including fireId (*int*), fire ignition (:obj:`datetime`), and fire latitude-longitude location (:obj:`GeographicPosition`)
    """

    def __init__(self, app, fires):
        self.app = app
        self.fires = fires

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks the simulation :obj:`datetime` against each scheduled fire ignition :obj:`datetime` for the scenario. If past the scheduled start of a fire, a :obj:`FireStarted` message is sent to *PREFIX/fire/location*:

        .. literalinclude:: /../../examples/firesat/fires/main_fire.py
            :lines: 51-66

        """
        if property_name == "time":
            if property_name == "time":
                new_fires = self.fires[
                    (self.fires.start <= new_value) & (self.fires.start > old_value)
                ]
            for index, fire in new_fires.iterrows():
                print(f"fireId: {fire.fireId}")
                self.app.send_message(
                    "location",
                    FireStarted(
                        fireId=fire.fireId,
                        start=fire.start,
                        latitude=fire.latitude,
                        longitude=fire.longitude,
                    ).json(),
                )

    def on_fire(self, channel, method, body):
        start = FireStarted.parse_raw(body)
        for key, fire in self.fires.iterrows():
            if key == start.fireId:
                self.fires["fireState"][key] = FireState.started
                break

    def on_detected(self, channel, method, body):
        detect = FireDetected.parse_raw(body)
        for key, fire in self.fires.iterrows():
            if key == detect.fireId:
                self.fires["fireState"][key] = FireState.detected
                self.fires["detected"][key] = detect.detected
                self.fires["detected_by"][key] = detect.detected_by
                break

    def on_reported(self, channel, method, body):
        report = FireReported.parse_raw(body)
        for key, fire in self.fires.iterrows():
            if key == report.fireId:
                self.fires["fireState"][key] = FireState.reported
                self.fires["reported"][key] = report.reported
                self.fires["reported_by"][key] = report.reported_by
                self.fires["reported_to"][key] = report.reported_to
                break


def on_fire(channel, method, properties, body):
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_fire(channel, method, body)

def on_detected(channel, method, properties, body):
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_detected(channel, method, body)

def on_reported(channel, method, properties, body):
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_reported(channel, method, body)



# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # # Note that these are loaded from a .env file in current working directory
    # credentials = dotenv_values(".env")
    # HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    # USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # # set the client credentials
    # config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, False)

    # Load credentials from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    CLIENT_ID = credentials["CLIENT_ID"]
    CLIENT_SECRET_KEY = credentials["CLIENT_SECRET_KEY"]
    VIRTUAL_HOST = credentials["VIRTUAL_HOST"]
    IS_TLS = credentials["IS_TLS"].lower() == 'true'  # Convert to boolean

    # Set the client credentials from the config file
    config = ConnectionConfig(
        USERNAME,
        PASSWORD,
        HOST,
        PORT,
        CLIENT_ID,
        CLIENT_SECRET_KEY,
        VIRTUAL_HOST,
        IS_TLS)
    
    # create the managed application
    app = ManagedApplication("fire")

    # import csv file from fire_scenarios subdirectory with scenario defining locations and ignition datetimes of fires
    csvFile = importlib.resources.open_text("fire_scenarios", "first5days.csv")

    # Read the csv file and convert to a DataFrame with initial column defining the index
    df = pd.read_csv(csvFile, index_col=0)
    fires = pd.DataFrame(
        data={
            "fireId": df.index,
            "start": pd.to_datetime(df["start_time"], utc=True),
            "latitude": df["latitude"],
            "longitude": df["longitude"],
        }
    )

    # Add blank columns to data frame for logging state, detection time, reporting time, and detector satellite
    fires.insert(1, "fireState", FireState.undefined)
    fires.insert(3, "detected", datetime(1900, 1, 1, tzinfo=timezone.utc))
    fires.insert(4, "detected_by", "Undetected")
    fires.insert(5, "reported", datetime(1900, 1, 1, tzinfo=timezone.utc))
    fires.insert(6, "reported_by", "Unreported")
    fires.insert(7, "reported_to", None)

    # add the environment observer to monitor for fire status events
    app.simulator.add_observer(Environment(app, fires))

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
    
    app.ready()
    
    # add message callbacks for fire ignition, detection, and report
    app.add_message_callback("fire", "location", on_fire)
    app.add_message_callback("constellation", "detected", on_detected)
    app.add_message_callback("constellation", "reported", on_reported)

    app.channel.start_consuming()

    # while True:
        # pass