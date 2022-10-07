from datetime import timedelta
import logging
import threading
import traceback

from .application import Application
from .schemas import InitCommand, StartCommand, StopCommand, UpdateCommand

logger = logging.getLogger(__name__)


class ManagedApplication(Application):
    """
    Managed NOS-T Application.

    This object class defines the basic functionality for a NOS-T application
    that utilizes an external Manager to command simulator execution.

    Attributes:
        prefix (str) : The test run namespace (prefix)
        simulator (:obj:`Simulator`): Application simulator defined in the *Simulator* class
        client (:obj:`Client`): Application MQTT client
        app_name (str): Test run application name
        app_description (str): Test run application description (optional)
        time_status_step (:obj:`timedelta`): Scenario duration between time status messages
        time_status_init (:obj:`datetime`): Scenario time of first time status message
        time_step (:obj:`timedelta`): Scenario time step used in execution
    """

    def __init__(self, app_name, app_description=None):
        super().__init__(app_name, app_description)
        self.time_step = None
        self._sim_start_time = None
        self._sim_stop_time = None

    def start_up(
        self,
        prefix,
        config,
        set_offset=True,
        time_status_step=None,
        time_status_init=None,
        shut_down_when_terminated=False,
        time_step=timedelta(seconds=1),
        manager_app_name="manager",
    ):
        """
        Starts up the application by connecting to message broker, starting a background event loop,
        subscribing to manager events, and registering callback functions.

        Args:
            prefix (str): The test run namespace (prefix)
            config (:obj:`ConnectionConfig`): The connection configuration
            set_offset (bool): True, if the system clock offset shall be set
            time_status_step (:obj:`timedelta`): Scenario duration between time status messages
            time_status_init (:obj:`datetime`): Scenario time for first time status message
            shut_down_when_terminated (bool) : True, if the application should shut down when the simulation is terminated
            time_step (:obj:`timedelta`): Scenario time step used in execution
            manager_app_name (str): Name of the manager application (Default: manager)
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

    def shut_down(self):
        """
            shut_down shuts down the application by stopping the background event loop, and also disconnects
            the application from the message broker
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

    def on_manager_init(self, client, userdata, message):
        """
        on_manager_init is a callback function for the referenced application ('self') to
        respond to an initilize command sent from the manager. It will parse the payload to extract sim_start_time
        and sim_stop_time to determine application initilize time within the simulation.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            message (:obj:`MQTTMessage`): The MQTT message
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

    def on_manager_start(self, client, userdata, message):
        """
        on_manager_start is a callback function for the referenced application ('self') to
        respond to a start command sent from the manager. It will parse the payload to extract sim_start_time
        and sim_stop_time for the beginning of the simulation, and will determine the duration of the simulation, the
        timedelta for the time_step, the wallclock_epoch, and the time_scale_factor responsbible for the speed of the simulation.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            message (:obj:`MQTTMessage`): The MQTT message
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

    def on_manager_stop(self, client, userdata, message):
        """
        on_manager_stop is a callback function for the referenced application ('self') to
        respond to a stop command sent from the manager. It will parse the payload to extract the new sim_stop_time.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            message (:obj:`MQTTMessage`): The MQTT message
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

    def on_manager_update(self, client, userdata, message):
        """
        on_manager_update is a callback function for the referenced application ('self') to
        respond to an update command sent from the manager, intended to update the time_scale_factor.
        It will parse the payload to extract the new time_scale_factor.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            message (:obj:`MQTTMessage`): The MQTT message
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
