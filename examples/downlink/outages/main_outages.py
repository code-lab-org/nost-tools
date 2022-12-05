# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of satellites for monitoring fires propagated from Two-Line Elements (TLEs)*

    The application contains one :obj:`Constellation` (:obj:`Entity`) object class, one :obj:`PositionPublisher` (:obj:`WallclockTimeIntervalPublisher`), and two :obj:`Observer` object classes to monitor for :obj:`FireDetected` and :obj:`FireReported` events, respectively. The application also contains several methods outside of these classes, which contain standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson.

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

logging.basicConfig(level=logging.INFO)
random.seed(72)

# define an observer to manage fire updates and record to a dataframe fires
class Scheduler(Observer):
    """
    *The Scheduler object class inherits properties from the Entity object class in the NOS-T tools library*

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
        Callback function appends a dictionary of information for a new ground station to grounds :obj:`list` when message detected on the *PREFIX/ground/location* topic. Ground station information is published at beginning of simulation, and the :obj:`list` is converted to a :obj:`DataFrame` when the Constellation is initialized.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        location = GroundLocation.parse_raw(message.payload)
        # if location.groundId in self.grounds.groundId:
        #     self.grounds[
        #         self.grounds.groundId == location.groundId
        #     ].latitude = location.latitude
        #     self.grounds[
        #         self.grounds.groundId == location.groundId
        #     ].longitude = location.longitude
        #     self.grounds[
        #         self.grounds.groundId == location.groundId
        #     ].elevAngle = location.elevAngle
        #     self.grounds[
        #         self.grounds.groundId == location.groundId
        #     ].operational = location.operational
        #     self.grounds[
        #         self.grounds.groundId == location.groundId
        #     ].downlinkRate = location.downlinkRate
        #     self.grounds[
        #         self.grounds.groundId == location.groundId
        #     ].costPerSecond = location.costPerSecond
        #     print(f"Station {location.groundId} updated at time {self.get_time()}.")
        # else:
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

        In this instance, the callback function checks the simulation :obj:`datetime` against each scheduled outage :obj:`datetime` for the scenario. If past the scheduled start of an outage, a :obj:`OutageReport` message is sent to *PREFIX/outage/report*:

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
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions

    """
    def __init__(self, app, scheduler, probOutage, time_status_step=None, time_status_init=None):
        super().__init__(app, time_status_step, time_status_init)
        self.app = app
        self.scheduler = scheduler
        self.probOutage = probOutage
        
    def publish_message(self):
        """
        *Abstract publish_message method inherited from the ScenarioTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

        This method sends a message to the *PREFIX/constellation/location* topic for each satellite in the constellation (:obj:`Constellation`), including:

        Args:
            id (:obj:`list`): list of unique *int* ids for each satellite in the constellation
            names (:obj:`list`): list of unique *str* for each satellite in the constellation - *NOTE:* must be same length as **id**
            positions (:obj:`list`): list of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
            radius (:obj:`list`): list of the radius (meters) of the nadir pointing sensors circular view of observation for each satellite in the constellation - *NOTE:* must be same length as **id**
            commRange (:obj:`list`): list of *bool* indicating each satellites visibility to *any* ground station - *NOTE:* must be same length as **id**
            time (:obj:`datetime`): current scenario :obj:`datetime`

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
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

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
    app.simulator.add_observer(Randomizer(app, outageScheduler, 0.003, time_status_step=timedelta(seconds=3)*SCALE, time_status_init=datetime(2022, 11, 30, 7, 20, tzinfo=timezone.utc)))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2022, 11, 30, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )
    
    # add message callbacks
    app.add_message_callback("ground", "location", outageScheduler.on_ground)