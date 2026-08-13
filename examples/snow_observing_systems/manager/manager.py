import logging

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.manager import Manager

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Load the connection and execution configuration. The scenario window, time
    # scale, and required applications all come from the YAML file, so this
    # script does not need to be edited to change a test case.
    config = ConnectionConfig(yaml_file="sos.yaml")

    # create the manager application from the template in the tools library
    manager = Manager()

    # add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # start up the manager on the prefix defined in the YAML file
    manager.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    # execute a test plan using the parameters in the YAML file
    manager.execute_test_plan()
