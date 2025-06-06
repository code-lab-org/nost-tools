# -*- coding: utf-8 -*-
"""
*This application demonstrates a network of ground stations given geospatial locations, minimum elevation angle constraints, and operational status.*

The application contains a :obj:`GroundNetwork` (:obj:`Observer`) object class to track the state of each constituent ground station, as well as the :obj:`LinkStartObserver` and :obj:`LinkEndObserver` object classes that monitor Acquisition of Signal (AOS) and Loss of Signal (LOS) events, respectively.

"""

import logging

import pandas as pd
from ground_config_files.schemas import (  # type: ignore
    GroundLocation,
    LinkCharge,
    LinkStart,
    OutageReport,
    OutageRestore,
    SatelliteReady,
    SatelliteState,
)

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.managed_application import ManagedApplication  # type: ignore
from nost_tools.observer import Observable, Observer  # type: ignore
from nost_tools.simulator import Mode, Simulator  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# define an observer to manage ground updates
class GroundNetwork(Observable, Observer):
    """
    *The GroundNetwork object class inherits properties from the Observer object class in the NOS-T tools library.*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions.
        grounds (:obj:`DataFrame`): DataFrame of ground station information including groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*).
    """

    PROPERTY_IN_RANGE = "linkOn"
    PROPERTY_OUT_OF_RANGE = "linkCharge"

    def __init__(self, app, grounds):
        super().__init__()
        self.app = app
        self.grounds = grounds
        self.satelliteIds = []
        self.satelliteNames = []
        self.ssrCapacity = []
        self.outages = []
        self.restores = []
        self.cumulativeCosts = 0.00

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class.*

        In this instance, the callback function checks when the **PROPERTY_MODE** switches to **EXECUTING** to send a :obj:`GroundLocation` message to the *PREFIX/ground/location* topic.

        """
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.EXECUTING:
            for index, ground in self.grounds.iterrows():
                self.app.send_message(
                    self.app.app_name,
                    "location",
                    GroundLocation(
                        groundId=ground.groundId,
                        latitude=ground.latitude,
                        longitude=ground.longitude,
                        elevAngle=ground.elevAngle,
                        operational=ground.operational,
                        downlinkRate=ground.downlinkRate,
                        costPerSecond=ground.costPerSecond,
                        costMode=ground.costMode,
                    ).model_dump_json(),
                )

    def on_ready(self, ch, method, properties, body):
        """
        Callback function for subscribed messages on the *PREFIX/constellation/ready* topic.

        For each message received, appends a satellite and its specs to internal lists.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used).
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes.

        """
        body = body.decode("utf-8")
        ready = SatelliteReady.model_validate_json(body)
        self.satelliteIds.append(ready.id)
        self.satelliteNames.append(ready.name)
        self.ssrCapacity.append(ready.ssr_capacity)

    def all_ready(self, ch, method, properties, body):
        """
        Callback function for subscribed messages on the *PREFIX/constellation/allReady* topic.

        This is a simple trigger that the list of constituent satellites have been finalized and appended to lists.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used).
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes.

        """
        self.groundTimes = {j: [] for j in self.satelliteNames}
        self.satView = {k: {"on": False, "linkCount": 0} for k in self.satelliteNames}
        self.cumulativeCostBySat = {l: 0.00 for l in self.satelliteNames}
        for i, l in enumerate(self.satelliteNames):
            self.app.send_message(
                self.app.app_name,
                "linkStart",
                LinkStart(
                    groundId=-1,
                    satId=i,
                    satName=l,
                    linkId=-1,
                    start=self.app.simulator.get_time(),
                    data=0.0,
                ).model_dump_json(),
            )
            self.app.send_message(
                self.app.app_name,
                "linkCharge",
                LinkCharge(
                    groundId=-1,
                    satId=i,
                    satName=l,
                    linkId=-1,
                    end=self.app.simulator.get_time(),
                    duration=0.0,
                    dataOffload=0.0,
                    downlinkCost=0.00,
                    cumulativeCostBySat=self.cumulativeCostBySat[l],
                    cumulativeCosts=0.00,
                ).model_dump_json(),
            )
            logger.info("ground.linkCharge message sent.")

    def on_commRange(self, ch, method, properties, body):
        """
        Callback function triggered by every :obj:`SatelliteState` message received on the *PREFIX/constellation/location* topic.

        Checks for changes in switch states and records timestamps of state transitions.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used).
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes.

        """
        body = body.decode("utf-8")
        satInView = SatelliteState.model_validate_json(body)
        if self.satView[satInView.name]["on"]:
            if not satInView.commRange:
                self.groundTimes[satInView.name][
                    self.satView[satInView.name]["linkCount"]
                ]["end"] = satInView.time
                self.groundTimes[satInView.name][
                    self.satView[satInView.name]["linkCount"]
                ]["duration"] = (
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["end"]
                    - self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["start"]
                ).total_seconds()
                self.groundTimes[satInView.name][
                    self.satView[satInView.name]["linkCount"]
                ]["dataOffload"] = (
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["duration"]
                    * self.grounds["downlinkRate"][
                        self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["groundId"]
                    ]
                )
                self.groundTimes[satInView.name][
                    self.satView[satInView.name]["linkCount"]
                ]["downlinkCost"] = (
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["duration"]
                    * self.grounds["costPerSecond"][
                        self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["groundId"]
                    ]
                )
                if (
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["dataOffload"]
                    > self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["initialData"]
                ):
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["dataOffload"] = self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ][
                        "initialData"
                    ]
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["downlinkCost"] = (
                        self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["dataOffload"]
                        / self.grounds["downlinkRate"][
                            self.groundTimes[satInView.name][
                                self.satView[satInView.name]["linkCount"]
                            ]["groundId"]
                        ]
                    ) * self.grounds[
                        "costPerSecond"
                    ][
                        self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["groundId"]
                    ]
                if (
                    self.grounds["costMode"][
                        self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["groundId"]
                    ]
                    == "continuous"
                ):
                    self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["downlinkCost"] = 0.00
                self.cumulativeCostBySat[satInView.name] = (
                    self.cumulativeCostBySat[satInView.name]
                    + self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["downlinkCost"]
                )
                self.cumulativeCosts = (
                    self.cumulativeCosts
                    + self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["downlinkCost"]
                )
                self.notify_observers(
                    self.PROPERTY_OUT_OF_RANGE,
                    None,
                    {
                        "groundId": self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["groundId"],
                        "satId": satInView.id,
                        "satName": satInView.name,
                        "linkId": self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["linkId"],
                        "end": self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["end"],
                        "duration": self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["duration"],
                        "dataOffload": self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["dataOffload"],
                        "downlinkCost": self.groundTimes[satInView.name][
                            self.satView[satInView.name]["linkCount"]
                        ]["downlinkCost"],
                        "cumulativeCostBySat": self.cumulativeCostBySat[satInView.name],
                        "cumulativeCosts": self.cumulativeCosts,
                    },
                )
                self.satView[satInView.name]["on"] = False
                self.satView[satInView.name]["linkCount"] = (
                    self.satView[satInView.name]["linkCount"] + 1
                )

        elif satInView.commRange:
            self.groundTimes[satInView.name].append(
                {
                    "groundId": satInView.groundId,
                    "satId": satInView.id,
                    "satName": satInView.name,
                    "linkId": self.satView[satInView.name]["linkCount"],
                    "start": satInView.time,
                    "end": None,
                    "duration": None,
                    "initialData": satInView.capacity_used,
                    "dataOffload": None,
                    "downlinkCost": None,
                },
            )
            self.satView[satInView.name]["on"] = True
            self.notify_observers(
                self.PROPERTY_IN_RANGE,
                None,
                {
                    "groundId": self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["groundId"],
                    "satId": satInView.id,
                    "satName": satInView.name,
                    "linkId": self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["linkId"],
                    "start": satInView.time,
                    "data": self.groundTimes[satInView.name][
                        self.satView[satInView.name]["linkCount"]
                    ]["initialData"],
                },
            )

    def on_outage(self, ch, method, properties, body):
        """
        Callback function triggered by every :obj:`OutageReport` message received on the *PREFIX/outages/report* topic.

        Appends a new outage dictionary to a list of outage dictionaries. Used to indicate which ground station has become inoperable and the expected outage duration.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used).
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes.

        """
        body = body.decode("utf-8")
        outageReport = OutageReport.model_validate_json(body)
        self.grounds.loc[outageReport.groundId, "operational"] = False
        self.outages.append(
            {
                "groundId": outageReport.groundId,
                "outageStart": outageReport.outageStart,
                "outageDuration": outageReport.outageDuration,
                "outageEnd": outageReport.outageEnd,
            },
        )

    def on_restore(self, ch, method, properties, body):
        """
        Callback function triggered by every :obj:`OutageRestore` message received on the *PREFIX/outages/restore* topic.

        Notifies observers of restored service at a previously inoperable ground station.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used).
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes.

        """
        body = body.decode("utf-8")
        outageRestore = OutageRestore.model_validate_json(body)
        self.grounds.loc[outageRestore.groundId, "operational"] = True
        self.restores.append(
            {"groundId": outageRestore.groundId, "outageEnd": outageRestore.outageEnd},
        )

    def fixedCost(self, ch, method, properties, body):
        """
        Callback function triggered by every :obj:`LinkCharge` message sent to the *PREFIX/constellation/linkCharge* topic.

        Messages only apply to satellites operating under fixed contracts. These messages are intended to create a continuous cost curve for the visualizations.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used).
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes.

        """
        body = body.decode("utf-8")
        fixedCharge = LinkCharge.model_validate_json(body)
        self.cumulativeCostBySat[fixedCharge.satName] = fixedCharge.cumulativeCostBySat
        self.cumulativeCosts = fixedCharge.cumulativeCosts


class LinkStartObserver(Observer):
    """
    *This object class inherits properties from the Observer object class from the observer template in the NOS-T tools library.*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions.

    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class in NOS-T tools library.*

        In this instance, the callback function checks for notification of the PROPERTY_IN_RANGE and publishes :obj:`LinkStart` message to *PREFIX/ground/linkStart* topic.

        """
        if property_name == GroundNetwork.PROPERTY_IN_RANGE:
            self.app.send_message(
                self.app.app_name,
                "linkStart",
                LinkStart(
                    groundId=new_value["groundId"],
                    satId=new_value["satId"],
                    satName=new_value["satName"],
                    linkId=new_value["linkId"],
                    start=new_value["start"],
                    data=new_value["data"],
                ).model_dump_json(),
            )


class LinkEndObserver(Observer):
    """
    *This object class inherits properties from the Observer object class from the observer template in the NOS-T tools library.*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions.

    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class in NOS-T tools library*

        In this instance, the callback function checks for notification of the PROPERTY_OUT_OF_RANGE and publishes :obj:`LinkCharge` message to *PREFIX/ground/linkCharge* topic.

        """
        if property_name == GroundNetwork.PROPERTY_OUT_OF_RANGE:
            self.app.send_message(
                self.app.app_name,
                "linkCharge",
                LinkCharge(
                    groundId=new_value["groundId"],
                    satId=new_value["satId"],
                    satName=new_value["satName"],
                    linkId=new_value["linkId"],
                    end=new_value["end"],
                    duration=new_value["duration"],
                    dataOffload=new_value["dataOffload"],
                    downlinkCost=new_value["downlinkCost"],
                    cumulativeCostBySat=new_value["cumulativeCostBySat"],
                    cumulativeCosts=new_value["cumulativeCosts"],
                ).model_dump_json(),
            )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Define application name
    NAME = "ground"

    # Load config
    config = ConnectionConfig(yaml_file="downlink.yaml", app_name=NAME)

    # Create the managed application
    app = ManagedApplication(app_name=NAME)

    # Get the ground station information from the configuration
    stations = config.rc.application_configuration["stations"]
    GROUND = pd.json_normalize(stations)[
        [
            "groundId",
            "latitude",
            "longitude",
            "elevAngle",
            "operational",
            "downlinkRate",
            "costPerSecond",
            "costMode",
        ]
    ]

    # Initialize the GroundNetwork Observable
    groundNetwork = GroundNetwork(app, GROUND)

    # Add observers for in-range and out-of-range switches to the groundNetwork object class
    groundNetwork.add_observer(LinkStartObserver(app))
    groundNetwork.add_observer(LinkEndObserver(app))

    # Add the groundNetwork observer to monitor simulation for switch to EXECUTING mode
    app.simulator.add_observer(groundNetwork)

    # Add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    # Add message callbacks
    app.add_message_callback("constellation", "ready", groundNetwork.on_ready)
    app.add_message_callback("constellation", "allReady", groundNetwork.all_ready)
    app.add_message_callback("constellation", "location", groundNetwork.on_commRange)
    app.add_message_callback("constellation", "linkCharge", groundNetwork.fixedCost)
    app.add_message_callback("outage", "report", groundNetwork.on_outage)
    app.add_message_callback("outage", "restore", groundNetwork.on_restore)

    while True:
        pass
