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
from nost_tools.observer import Observer
from nost_tools.simulator import Mode, Simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyTimeScaleUpdater(Observer):
    """
    Observer that automatically speeds up the time scale factor at the start of each day.
    """

    def __init__(
        self,
        manager: Manager,
        fast_scale_factor: float = 120.0,
        slow_scale_factor: float = 60.0,
    ):
        """
        Initialize the daily time scale updater.

        Args:
            manager (Manager): The manager instance to send update requests
            fast_scale_factor (float): Time scale factor for daytime (default 120.0)
            slow_scale_factor (float): Time scale factor for nighttime (default 60.0)
        """
        self.manager = manager
        self.slow_scale_factor = slow_scale_factor
        self.fast_scale_factor = fast_scale_factor
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
            current_hour = current_sim_time.hour

            # Determine desired time scale based on time of day
            if 7 <= current_hour < 10 or 17 <= current_hour < 24:
                desired_time_scale = self.slow_scale_factor
            else:
                desired_time_scale = self.fast_scale_factor

            # Check if we've crossed into a new day or need to change time scale
            if (
                self.last_day_checked != current_day
                or self.current_time_scale != desired_time_scale
            ):

                logger.info(
                    f"Time scale update needed at {current_sim_time}: "
                    f"{self.current_time_scale} -> {desired_time_scale}"
                )

                # Request the time scale update from the manager
                self.manager.update(desired_time_scale, current_sim_time)

                # Update tracking variables
                self.last_day_checked = current_day
                self.current_time_scale = desired_time_scale


if __name__ == "__main__":
    # Load config
    config = ConnectionConfig(yaml_file="firesat.yaml")

    # Create the manager application
    manager = Manager()

    # Add the daily time scale updater observer
    manager.simulator.add_observer(
        DailyTimeScaleUpdater(
            manager,
            slow_scale_factor=config.rc.simulation_configuration.execution_parameters.manager.time_scale_factor,
            fast_scale_factor=120.0,
        )
    )

    # Add a shutdown observer to shut down after a single test case
    manager.simulator.add_observer(ShutDownObserver(manager))

    # Start up the manager
    manager.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    manager.execute_test_plan()
