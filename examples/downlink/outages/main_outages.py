# -*- coding: utf-8 -*-
"""
    *This application implements scheduled and/or random outages at constituent ground stations.*

    The application contains one :obj:`Scheduler` (:obj:`Observer`) object class to monitor the time for outages pre-defined before the simulation begins and one :obj:`Randomizer` (:obj:`ScenarioIntervalPublisher`) object class for executing random Bernoulli trials to trigger randomized outages dynamically during the simulation.

"""

import logging
import random
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
import pandas as pd

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import ScenarioTimeIntervalPublisher

import importlib.resources

from outages_config_files.schemas import (
    GroundLocation,
    OutageReport,
    OutageRestore
)
from outages_config_files.config import (
    PREFIX,
    NAME,
    SCALE
)

import outages_scenarios

logging.basicConfig(level=logging.INFO)
random.seed(72)

# define an observer to manage fire updates and record to a dataframe fires
class Scheduler(Observer):
    """
    *The Scheduler object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        scheduled_outages (:obj:`DataFrame`): Dataframe of scenario scheduled outages including groundId (*int*), outageStart (:obj:`datetime`), outageDuration (:obj:`timedelta`), outageEnd (:obj:`datetime`)
    """

    def __init__(self, app, name, scheduled_outages):
        super().__init__()
        self.app = app
        self.scheduled_outages = scheduled_outages
        self.grounds = []

    def on_ground(self, client, userdata, message):
        """
        Callback function appends a dictionary of information for a new ground station to grounds :obj:`list` when :obj:`GroundLocation` message detected on the *PREFIX/ground/location* topic. Ground station information is published at beginning of simulation, and the completed :obj:`list` is converted to a :obj:`DataFrame`.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        location = GroundLocation.parse_raw(message.payload)
        self.grounds.append(
            {
                "groundId": location.groundId,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "elevAngle": location.elevAngle,
                "operational": location.operational,
                "downlinkRate": location.downlinkRate,
                "costPerSecond": location.costPerSecond,
                "costMode": location.costMode
            }
        )
        print(f"Station {location.groundId} registered at time {self.app.simulator.get_time()}.")
    
    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks the simulation :obj:`datetime` against each scheduled outage :obj:`datetime` for the scenario. If past the scheduled start of an outage, an :obj:`OutageReport` message is sent to *PREFIX/outage/report*:

        """
        if property_name == "time":
            if property_name == "time":
                for index, outage in self.scheduled_outages.iterrows():
                    if (outage.outageStart <= new_value) & (outage.outageStart > old_value):
                        self.app.send_message(
                            "report",
                            OutageReport(
                                groundId=outage.groundId,
                                outageStart=outage.outageStart,
                                outageDuration=outage.outageDuration,
                                outageEnd=outage.outageEnd,
                            ).json(),
                        )
                    if (outage.outageEnd <= new_value) & (outage.outageEnd > old_value):
                        self.app.send_message(
                            "restore",
                            OutageRestore(
                                groundId=outage.groundId,
                                outageEnd=outage.outageEnd
                            ).json()
                        )
        
class Randomizer(ScenarioTimeIntervalPublisher):
    """
    *This object class inherits properties from the ScenarioTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions.
        scheduler (:obj:`Scheduler`): A Scheduler object class must be added to the publisher.
        probOutage (float): A value between 0 and 1 that sets the probability of an outage for each random Bernoulli trial.
        time_status_step (:obj:`timedelta`): Optional duration between time status 'heartbeat' messages.
        time_status_init (:obj:`datetime`): Optional scenario :obj:`datetime` for publishing the first time status 'heartbeat' message.

    """
    def __init__(self, app, scheduler, probOutage, time_status_step=None, time_status_init=None):
        super().__init__(app, time_status_step, time_status_init)
        self.app = app
        self.scheduler = scheduler
        self.probOutage = probOutage
        
    def publish_message(self):
        """
        *Abstract publish_message method inherited from the ScenarioTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

        This method executes a random Bernoulli trial for *each* ground station at regular scenario time intervals. The probability of outage is typically set to a very low threshold and :obj:`OutageReport` messages are **only** sent when the random float between 0 and 1 is less than this defined threshold.

        """
        for i, ground in enumerate(self.scheduler.grounds):
            if ground["operational"]:
                randomDraw = random.random()
                if randomDraw <= self.probOutage:
                    timeOutage = self.app.simulator.get_time()
                    durationOutage = timedelta(hours=3)
                    endOutage = timeOutage + durationOutage
                    self.scheduler.scheduled_outages.append(
                        {
                            "groundId":ground["groundId"],
                            "outageStart":timeOutage,
                            "outageDuration":durationOutage,
                            "outageEnd":endOutage
                            },
                        ignore_index=True
                    )
                    self.app.send_message(
                        "report",
                        OutageReport(
                            groundId = ground["groundId"],
                            outageStart = timeOutage,
                            outageDuration = durationOutage,
                            outageEnd = endOutage
                        ).json()
                    )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication(NAME)
    
    # import csv file from outages_scenarios subdirectory with scenario defining groundId and datetimes of outages
    csvFile = importlib.resources.open_text("outages_scenarios", "only_random_outages.csv")
    # Read the csv file and convert to a DataFrame with initial column defining the index
    df = pd.read_csv(csvFile, index_col=0)
    schedule = pd.DataFrame(
        data={
            "outageId": df.index,
            "groundId": df["groundId"],
            "outageStart": pd.to_datetime(df["outageStart"], utc=True),
            "outageDuration": pd.to_timedelta(df["outageDuration"], unit="hours"),
            "outageEnd": pd.to_datetime(df["outageStart"], utc=True) + pd.to_timedelta(df["outageDuration"], unit="hours")
        }
    )
    
    # Initialize Outage Scheduler
    outageScheduler = Scheduler(app, NAME, schedule)

    # add the Scheduler entity to the application's simulator
    app.simulator.add_observer(outageScheduler)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))
    
    # add a ScenarioTimeIntervalPublisher for publishing random outages
    app.simulator.add_observer(Randomizer(app, outageScheduler, 0.03, time_status_step=timedelta(seconds=1)*SCALE, time_status_init=datetime(2023, 1, 23, 7, 20, tzinfo=timezone.utc)))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2023, 1, 23, 7, 30, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )
    
    # add message callbacks
    app.add_message_callback("ground", "location", outageScheduler.on_ground)