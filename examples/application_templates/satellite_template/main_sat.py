import logging
import time
from datetime import timedelta

from skyfield.api import load

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.managed_application import ManagedApplication
from nost_tools.simulator import Mode

from satellite import Satellite, StatusPublisher

logging.basicConfig(level=logging.INFO)

NAME = "satellite"

# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Load the connection and execution configuration. Passing app_name makes the
    # configuration_parameters for this application available on
    # config.rc.application_configuration.
    config = ConnectionConfig(yaml_file="template.yaml", app_name=NAME)

    # create the managed application
    app = ManagedApplication(NAME)

    # Name of the satellite to load from the Celestrak database
    name = config.rc.application_configuration["SATELLITE_NAME"]

    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    activesats = load.tle_file(activesats_url, reload=False)
    by_name = {sat.name: sat for sat in activesats}

    satellite = Satellite(app, name, ES=by_name[name])

    # add the satellite entity to the application's simulator
    app.simulator.add_entity(satellite)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state on a wallclock interval
    app.simulator.add_observer(StatusPublisher(app, satellite, timedelta(seconds=1)))

    # start up the application on the prefix defined in the YAML file. The time
    # step and time status interval come from the managed_applications section.
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(0.2)
