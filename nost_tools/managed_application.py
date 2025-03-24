"""
Provides a base application that manages communication between a simulator and broker.
"""

import logging
import threading
import traceback
from datetime import datetime, timedelta

from .application import Application
from .application_utils import ConnectionConfig
from .schemas import InitCommand, StartCommand, StopCommand, UpdateCommand

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
        self._sim_stop_time = None

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = None,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = None,
        time_step: timedelta = None,
        manager_app_name: str = None,
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
        if (
            set_offset is not None
            and time_status_step is not None
            and time_status_init is not None
            and shut_down_when_terminated is not None
            and time_step is not None
            and manager_app_name is not None
        ):
            self.set_offset = set_offset
            self.time_status_step = time_status_step
            self.time_status_init = time_status_init
            self.shut_down_when_terminated = shut_down_when_terminated
            self.time_step = time_step
            self.manager_app_name = manager_app_name
        else:
            self.config = config
            parameters = getattr(
                self.config.rc.simulation_configuration.execution_parameters,
                "managed_application",
                None,
            )
            logger.info(parameters)
            self.set_offset = parameters.set_offset
            self.time_status_step = parameters.time_status_step
            self.time_status_init = parameters.time_status_init
            self.shut_down_when_terminated = parameters.shut_down_when_terminated
            self.time_step = parameters.time_step
            self.manager_app_name = parameters.manager_app_name

        # start up base application
        super().start_up(
            prefix,
            config,
            self.set_offset,
            self.time_status_step,
            self.time_status_init,
            self.shut_down_when_terminated,
        )
        self.time_step = self.time_step
        self.manager_app_name = self.manager_app_name

        # Register callback functions
        self.add_message_callback(
            app_name=self.manager_app_name,
            app_topic="init",
            user_callback=self.on_manager_init,
        )
        self.add_message_callback(
            app_name=self.manager_app_name,
            app_topic="start",
            user_callback=self.on_manager_start,
        )
        self.add_message_callback(
            app_name=self.manager_app_name,
            app_topic="stop",
            user_callback=self.on_manager_stop,
        )
        self.add_message_callback(
            app_name=self.manager_app_name,
            app_topic="update",
            user_callback=self.on_manager_update,
        )

    def shut_down(self) -> None:
        """
        Shuts down the application by stopping the background event loop and disconnecting
        the application from the broker.
        """
        # shut down base application
        super().shut_down()

    def on_manager_init(self, ch, method, properties, body) -> None:
        """
        Callback function for the managed application to respond to an initilize command sent from the manager.
        Parses the scenario start/end times and signals ready.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # Parse message payload
            message = body.decode("utf-8")
            params = InitCommand.parse_raw(message).tasking_parameters
            # update default execution start/end time
            self._sim_start_time = params.sim_start_time
            self._sim_stop_time = params.sim_stop_time
            self.ready()

        except Exception as e:
            logger.error(
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_start(self, ch, method, properties, body) -> None:
        """
        Callback function for the managed application to respond to a start command sent from the manager.
        Parses the scenario start/end time, wallclock epoch, and time scale factor and executes
        the simulator in a background thread.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        # Parse message payload
        message = body.decode("utf-8")
        params = StartCommand.parse_raw(message).tasking_parameters
        logger.info(f"Received start command {params}")
        try:

            # check for optional start time
            if params.sim_start_time is not None:
                self._sim_start_time = params.sim_start_time
                logger.info(f"Sim start time: {params.sim_start_time}")
            # check for optional end time
            if params.sim_stop_time is not None:
                self._sim_stop_time = params.sim_stop_time
                logger.info(f"Sim stop time: {params.sim_stop_time}")

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
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_stop(self, ch, method, properties, body) -> None:
        """
        Callback function for the managed application ('self') to respond to a stop command sent from the manager.
        Parses the end time and updates the simulator.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # Parse message payload
            message = body.decode("utf-8")
            params = StopCommand.model_validate_json(message).tasking_parameters
            logger.info(f"Received stop command {message}")
            # update execution end time
            self.simulator.set_end_time(params.sim_stop_time)
        except Exception as e:
            logger.error(
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_update(self, ch, method, properties, body) -> None:
        """
        Callback function for the managed application ('self') to respond to an update command sent from the manager.
        Parses the time scaling factor and scenario update time and updates the simulator.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # Parse message payload
            message = body.decode("utf-8")
            params = UpdateCommand.model_validate_json(message).tasking_parameters
            logger.info(f"Received update command {message}")
            # update execution time scale factor
            self.simulator.set_time_scale_factor(
                params.time_scaling_factor, params.sim_update_time
            )
        except Exception as e:
            logger.error(
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())
