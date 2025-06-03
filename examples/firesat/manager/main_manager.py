# -*- coding: utf-8 -*-
"""
*This application demonstrates a manager synchronizing a test case between disaggregated applications*

This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :obj:`ManagedApplication` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.

.. literalinclude:: /../../examples/firesat/manager/main_manager.py
    :lines: 11-

"""
import logging

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.manager import Manager

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Load config
    config = ConnectionConfig(yaml_file="firesat.yaml")

    # Create the manager application
    manager = Manager()

    # Add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # Start up the manager
    manager.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    manager.execute_test_plan()
