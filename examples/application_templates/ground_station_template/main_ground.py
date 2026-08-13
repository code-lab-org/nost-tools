# -*- coding: utf-8 -*-
import logging

import pandas as pd

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.managed_application import ManagedApplication
from nost_tools.observer import Observer
from nost_tools.simulator import Mode, Simulator

from ground_config_files.schemas import GroundLocation

logging.basicConfig(level=logging.INFO)

NAME = "ground"


# define an observer to manage ground updates
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        grounds (:obj:`DataFrame`): DataFrame of ground station information including groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), and min_elevation (*float*) angle constraints
    """

    def __init__(self, app, grounds):
        self.app = app
        self.grounds = grounds

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks when the **PROPERTY_MODE** switches to **EXECUTING** to send a :obj:`GroundLocation` message to the *PREFIX/ground/location* topic. These locations are published as soon as the execution starts. As modeled here, the number, location, and elevation angle for each ground station will not change throughout the test case.

            .. literalinclude:: /../../examples/application_templates/ground_station_template/main_ground.py
                :lines: 45-55

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
                    ).json(),
                )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Load the connection and execution configuration. Passing app_name makes the
    # configuration_parameters for this application available on
    # config.rc.application_configuration.
    config = ConnectionConfig(yaml_file="template.yaml", app_name=NAME)

    # create the managed application
    app = ManagedApplication(NAME)

    # read the ground station locations from the configuration
    stations = config.rc.application_configuration["stations"]
    GROUND = pd.json_normalize(stations)[
        ["groundId", "latitude", "longitude", "elevAngle"]
    ]

    # add the environment observer to monitor simulation for switch to EXECUTING mode
    app.simulator.add_observer(Environment(app, GROUND))

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on the prefix defined in the YAML file. The time
    # step and time status interval come from the managed_applications section.
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )
