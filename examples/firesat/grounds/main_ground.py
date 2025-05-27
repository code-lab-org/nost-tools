# -*- coding: utf-8 -*-
"""
*This application models a ground stations at the Svalbard Satellite Station location with minimum elevation angle constraints.*

The application contains one class, the :obj:`Environment` class, which waits for a message from the manager that indicates the beginning of the simulation execution. The application publishes the ground station information once, at the beginning of the simulation.

"""

import logging

from ground_config_files.config import GROUND
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
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.EXECUTING:
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


if __name__ == "__main__":
    # Load config
    config = ConnectionConfig(yaml_file="firesat.yaml")

    # Define the simulation parameters
    NAME = "ground"

    # create the managed application
    app = ManagedApplication(NAME)

    # add the environment observer to monitor simulation for switch to EXECUTING mode
    app.simulator.add_observer(Environment(app, GROUND))

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
        True,
    )

    while True:
        pass
