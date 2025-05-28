# -*- coding: utf-8 -*-
"""
*This application demonstrates a manager synchronizing a test case between disaggregated applications*

This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :obj:`ManagedApplication` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.

.. literalinclude:: /../../manager/main_manager.py
    :lines: 12-

"""

import json
import logging

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.manager import Manager

logging.basicConfig(level=logging.INFO)


def on_ready(ch, method, properties, body):
    print("Manager received Ready status message from heartbeat application")


def on_mode(ch, method, properties, body):
    data = json.loads(body.decode("utf-8"))
    print(data["properties"]["mode"])


def on_time(ch, method, properties, body):
    data = json.loads(body.decode("utf-8"))
    print("Manager received time status message from heartbeat application")


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Load config
    config = ConnectionConfig(yaml_file="scalability.yaml")

    # Define the simulation parameters
    NAME = "manager"

    # create the manager application from the template in the tools library
    manager = Manager()

    # add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # start up the manager on PREFIX from config file
    manager.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
        True,
    )
    manager.add_message_callback("status.hearbeat", "ready", on_ready)
    manager.add_message_callback("status.heartbeat", "mode", on_mode)
    # manager.add_message_callback("status.heartbeat", "time", on_time)

    manager.execute_test_plan()
