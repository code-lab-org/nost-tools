"""
Provides a base application that manages communication between a simulator and broker.
"""

from datetime import datetime, timezone, timedelta
import logging
from paho.mqtt.client import Client, MQTTMessage
import threading
import traceback

from nost_tools.application import Application
from nost_tools.application_utils import ConnectionConfig
from nost_tools.schemas import InitCommand, StartCommand, StopCommand, UpdateCommand

from dotenv import dotenv_values
from constellation_config_files.config import (
    PREFIX,
    NAME,
    SCALE,
)

import mgd_proj_sim

logger = logging.getLogger(__name__)


class ManagedApplication(Application):
    """
    Managed NOS-T Application.

    This object class defines the basic functionality for a NOS-T application
    that utilizes an external Manager to command simulator execution.

    Attributes:
        prefix (str): execution namespace (prefix)
        simulator (:obj:`Simulator`): simulator
        client (:obj:`Client`): MQTT client
        app_name (str): application name
        app_description (str): application description
        time_status_step (:obj:`timedelta`): scenario duration between time status messages
        time_status_init (:obj:`datetime`): scenario time of first time status message
        time_step (:obj:`timedelta`): scenario time step used in execution
    """

    def __init__(self, app_name: str, app_description: str = None):
        """
        Initializes a new managed application.

        Args:
            app_name (str): application name
            app_description (str): application description
        """
        super().__init__(app_name, app_description)
        self.time_step = None
        self._sim_start_time = None
        self._sim_stop_time = 10

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = True,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = False,
        time_step: timedelta = timedelta(seconds=1),
        manager_app_name: str = "manager",
    ) -> None:
        """
        Starts up the application by connecting to message broker, starting a background event loop,
        subscribing to manager events, and registering callback functions.

        Args:
            prefix (str): execution namespace (prefix)
            config (:obj:`ConnectionConfig`): connection configuration
            set_offset (bool): True, if the system clock offset shall be set using a NTP request prior to execution
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time for first time status message
            shut_down_when_terminated (bool): True, if the application should shut down when the simulation is terminated
            time_step (:obj:`timedelta`): scenario time step used in execution (Default: 1 second)
            manager_app_name (str): manager application name (Default: manager)
        """
        # start up base application
        super().start_up(
            prefix,
            config,
            set_offset,
            time_status_step,
            time_status_init,
            shut_down_when_terminated,
        )
        self.time_step = time_step
        self.manager_app_name = manager_app_name
        # subscribe to manager topics
        self.client.subscribe(f"{self.prefix}/{self.manager_app_name}/#")
        # register callback function for init command
        self.client.message_callback_add(
            f"{self.prefix}/{self.manager_app_name}/init", self.on_manager_init
        )
        # register callback function for start command
        self.client.message_callback_add(
            f"{self.prefix}/{self.manager_app_name}/start", self.on_manager_start
        )
        # register callback function for stop command
        self.client.message_callback_add(
            f"{self.prefix}/{self.manager_app_name}/stop", self.on_manager_stop
        )
        # register callback function for update command
        self.client.message_callback_add(
            f"{self.prefix}/{self.manager_app_name}/update", self.on_manager_update
        )

    def shut_down(self) -> None:
        """
            Shuts down the application by stopping the background event loop and disconnecting
            the application from the broker.
        """
        # unregister callback functions
        self.client.message_callback_remove(
            f"{self.prefix}/{self.manager_app_name}/init"
        )
        self.client.message_callback_remove(
            f"{self.prefix}/{self.manager_app_name}/start"
        )
        self.client.message_callback_remove(
            f"{self.prefix}/{self.manager_app_name}/stop"
        )
        self.client.message_callback_remove(
            f"{self.prefix}/{self.manager_app_name}/update"
        )
        # shut down base application
        super().shut_down()

    def on_manager_init(self, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application to respond to an initilize command sent from the manager.
        Parses the scenario start/end times and signals ready.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object):  private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            # parse message payload
            params = InitCommand.parse_raw(message.payload).tasking_parameters
            # update default execution start/end time
            self._sim_start_time = params.sim_start_time
            self._sim_stop_time = params.sim_stop_time
            self.ready()
        except Exception as e:
            logger.error(
                f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_start(self, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application to respond to a start command sent from the manager. 
        Parses the scenario start/end time, wallclock epoch, and time scale factor and executes 
        the simulator in a background thread.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object): private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            # parse message payload
            params = StartCommand.parse_raw(message.payload).tasking_parameters
            logger.info(f"Received start command {message.payload}")
            # check for optional start time
            if params.sim_start_time is not None:
                self._sim_start_time = params.sim_start_time
            # check for optional end time
            if params.sim_stop_time is not None:
                self._sim_stop_time = params.sim_stop_time
            # start execution in a background thread
            threading.Thread(
                target=self.simulator.execute,
                kwargs={
                    "init_time": self._sim_start_time,
                    "duration": self._sim_stop_time - self._sim_start_time,
                    "time_step": self.time_step,
                    "wallclock_epoch": params.start_time,
                    "time_scale_factor": params.time_scaling_factor,
                },
            ).start()
        except Exception as e:
            logger.error(
                f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_stop(self, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application ('self') to respond to a stop command sent from the manager.
        Parses the end time and updates the simulator.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object): private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            # parse message payload
            params = StopCommand.parse_raw(message.payload).tasking_parameters
            logger.info(f"Received stop command {message.payload}")
            # update execution end time
            self.simulator.set_end_time(params.sim_stop_time)
        except Exception as e:
            logger.error(
                f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_update(self, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application ('self') to respond to an update command sent from the manager.
        Parses the time scaling factor and scenario update time and updates the simulator.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object): private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            # parse message payload
            params = UpdateCommand.parse_raw(message.payload).tasking_parameters
            logger.info(f"Received update command {message.payload}")
            # update execution time scale factor
            self.simulator.set_time_scale_factor(
                params.time_scaling_factor, params.sim_update_time
            )
        except Exception as e:
            logger.error(
                f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
            )
            print(traceback.format_exc())
            
# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("spacecraft")

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2020, 10, 24, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )

    # add message callbacks
    app.add_message_callback("manager", "status", mgd_proj_sim.simulate_adcs)

