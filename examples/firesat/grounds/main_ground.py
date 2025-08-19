# -*- coding: utf-8 -*-
"""
*This application models a ground stations at the Svalbard Satellite Station location with minimum elevation angle constraints.*

The application contains one class, the :obj:`Environment` class, which waits for a message from the manager that indicates the beginning of the simulation execution. The application publishes the ground station information once, at the beginning of the simulation.

"""

import logging
from datetime import timedelta

import pandas as pd
from ground_config_files.schemas import GroundLocation

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.managed_application import ManagedApplication
from nost_tools.observer import Observer
from nost_tools.simulator import Mode, Simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks when the **PROPERTY_MODE** switches to **EXECUTING** to send a :obj:`GroundLocation` message to the *PREFIX/ground/location* topic:

            .. literalinclude:: /../../examples/firesat/grounds/main_ground.py
                :pyobject: Environment.on_change
                :lines: 11-
        """
        if (
            property_name == Simulator.PROPERTY_MODE
            and new_value == Mode.EXECUTING
            and old_value != Mode.RESUMING
        ):
            logger.info("Grounds are operational")
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
                    ).model_dump_json(),
                )


class DailyFreeze(Observer):
    """
    Observer that automatically freezes the simulation at the start of each day.
    """

    def __init__(
        self, app: ManagedApplication, freeze_duration: timedelta = timedelta(hours=2)
    ):
        """
        Initialize the daily time scale updater.

        Args:
            manager (Manager): The manager instance to send update requests
            freeze_duration (timedelta): Duration to freeze the simulation at the start of each day (default 2 wall clock hours)
        """
        self.app = app
        self.freeze_duration = freeze_duration
        self.last_day_checked = None
        self.current_time_scale = None

    def on_change(self, source, property_name, old_value, new_value):
        """
        Callback when simulation properties change.

        Args:
            source: The object that changed
            property_name (str): Name of the property that changed
            old_value: Previous value
            new_value: New value
        """
        # Only respond to time changes when simulation is executing
        if (
            property_name == Simulator.PROPERTY_TIME
            and source.get_mode() == Mode.EXECUTING
            and new_value is not None
        ):

            current_sim_time = new_value
            current_day = current_sim_time.date()

            # Check if we've crossed into a new day or need to change time scale
            if self.last_day_checked != current_day:

                logger.info("Crossed into a new day, freezing scenario time.")
                # Request the time scale update from the manager
                self.app.request_freeze(
                    freeze_duration=self.freeze_duration,
                    sim_freeze_time=current_sim_time,
                )

                # Update tracking variables
                self.last_day_checked = current_day


if __name__ == "__main__":
    # Define application name
    NAME = "ground"

    # Load config
    config = ConnectionConfig(yaml_file="firesat.yaml", app_name=NAME)

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
        ]
    ]

    # Add the environment observer to monitor simulation for switch to EXECUTING mode
    app.simulator.add_observer(Environment(app, GROUND))

    # Add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # Add the daily time scale updater observer
    app.simulator.add_observer(DailyFreeze(app, freeze_duration=timedelta(minutes=1)))

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    while True:
        pass
