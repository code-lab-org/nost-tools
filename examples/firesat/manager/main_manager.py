import logging

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.manager import Manager

logging.basicConfig(level=logging.INFO)


def main():
    # Load config
    config = ConnectionConfig(yaml_file="firesat.yaml")

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

    manager.execute_test_plan()


if __name__ == "__main__":
    main()
