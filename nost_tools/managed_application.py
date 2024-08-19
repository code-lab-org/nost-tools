"""
Provides a base application that manages communication between a simulator and broker.
"""

from datetime import datetime, timedelta
import logging
from paho.mqtt.client import Client, MQTTMessage
import threading
import traceback

from .application import Application
from .application_utils import ConnectionConfig
from .schemas import InitCommand, StartCommand, StopCommand, UpdateCommand

import json

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

    def on_message(self, ch, method, properties, body):
        try:
            routing_key = method.routing_key
            if routing_key == f"{self.prefix}.{self.manager_app_name}.init":
                self.on_manager_init(ch, method, properties, body)
            elif routing_key == f"{self.prefix}.{self.manager_app_name}.start":
                self.on_manager_start(ch, method, properties, body)
            elif routing_key == f"{self.prefix}.{self.manager_app_name}.stop":
                self.on_manager_stop(ch, method, properties, body)
            elif routing_key == f"{self.prefix}.{self.manager_app_name}.update":
                self.on_manager_update(ch, method, properties, body)
        except Exception as e:
            print(f"Error handling message: {e}")


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
        topic = f"{self.prefix}.{self.manager_app_name}.#"
        queue_name = topic #".".join(topic.split(".") + ["queue"])

        # # Declare exchange and queue
        # self.channel.exchange_declare(exchange=self.manager_app_name, exchange_type='topic')
        # self.queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        # self.channel.queue_bind(exchange=self.manager_app_name, queue=self.queue, routing_key=f"{self.prefix}.{self.manager_app_name}.#")

        # Declare the exchange
        self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # # Declare the queue
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind the queue to the exchange with the routing key
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)
        
        
        # Register callback functions
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.on_message, auto_ack=True)

        # Start consuming
        # self.channel.start_consuming()
        
        # # register callback function for init command
        # self.add_message_callback(self.manager_app_name, 'init', self.on_manager_init)

        # # register callback function for start command
        # self.add_message_callback(self.manager_app_name, 'start', self.on_manager_start)

        # # register callback function for stop command
        # self.add_message_callback(self.manager_app_name, 'stop', self.on_manager_stop)

        # # register callback function for update command
        # self.add_message_callback(self.manager_app_name, 'update', self.on_manager_update)

        # self.channel.start_consuming()
    
        # subscribe to manager topics
        # self.client.subscribe(f"{self.prefix}/{self.manager_app_name}/#")

        # subscribe to manager topics
        # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')
        # self.channel.queue_declare(queue=queue_name, durable=True)

        # # Bind the queue to the exchange with the routing key pattern
        # self.channel.queue_bind(
        #     exchange=self.prefix,
        #     queue=queue_name,
        #     routing_key=topic
        # )

        # # register callback function for init command
        # # self.client.message_callback_add(
        # #     # f"{self.prefix}/{self.manager_app_name}/init", self.on_manager_init
        # #     f"{self.prefix}.{self.manager_app_name}.init", self.on_manager_init
        # # )
        # self.channel.queue_declare(queue=f"{self.prefix}.{self.manager_app_name}.init", durable=True)

        # # Bind the queue to the exchange with the routing key pattern
        # self.channel.queue_bind(
        #     exchange=self.prefix,
        #     queue=f"{self.prefix}.{self.manager_app_name}.init",
        #     routing_key=f"{self.prefix}.{self.manager_app_name}.init"
        # )
        # self.channel.basic_consume(queue=f"{self.prefix}.{self.manager_app_name}.init", on_message_callback=self.on_manager_init, auto_ack=True)

        # # register callback function for start command
        # # self.client.message_callback_add(
        # #     # f"{self.prefix}/{self.manager_app_name}/start", self.on_manager_start
        # #     f"{self.prefix}.{self.manager_app_name}.start", self.on_manager_start
        # # )
        # self.channel.queue_declare(queue=f"{self.prefix}.{self.manager_app_name}.start", durable=True)

        # # Bind the queue to the exchange with the routing key pattern
        # self.channel.queue_bind(
        #     exchange=self.prefix,
        #     queue=f"{self.prefix}.{self.manager_app_name}.start",
        #     routing_key=f"{self.prefix}.{self.manager_app_name}.start"
        # )
        # self.channel.basic_consume(queue=f"{self.prefix}.{self.manager_app_name}.start", on_message_callback=self.on_manager_start, auto_ack=True)

        # # register callback function for stop command
        # # self.client.message_callback_add(
        # #     # f"{self.prefix}/{self.manager_app_name}/stop", self.on_manager_stop
        # #     f"{self.prefix}.{self.manager_app_name}.stop", self.on_manager_stop
        # # )
        # self.channel.queue_declare(queue=f"{self.prefix}.{self.manager_app_name}.stop", durable=True)

        # # Bind the queue to the exchange with the routing key pattern
        # self.channel.queue_bind(
        #     exchange=self.prefix,
        #     queue=f"{self.prefix}.{self.manager_app_name}.stop",
        #     routing_key=f"{self.prefix}.{self.manager_app_name}.stop"
        # )
        # self.channel.basic_consume(queue=f"{self.prefix}.{self.manager_app_name}.stop", on_message_callback=self.on_manager_stop, auto_ack=True)

        # # register callback function for update command
        # # self.client.message_callback_add(
        # #     # f"{self.prefix}/{self.manager_app_name}/update", self.on_manager_update
        # #     f"{self.prefix}.{self.manager_app_name}.update", self.on_manager_update
        # # )
        # self.channel.queue_declare(queue=f"{self.prefix}.{self.manager_app_name}.update", durable=True)

        # # Bind the queue to the exchange with the routing key pattern
        # self.channel.queue_bind(
        #     exchange=self.prefix,
        #     queue=f"{self.prefix}.{self.manager_app_name}.update",
        #     routing_key=f"{self.prefix}.{self.manager_app_name}.update"
        # )
        # self.channel.basic_consume(queue=f"{self.prefix}.{self.manager_app_name}.update", on_message_callback=self.on_manager_update, auto_ack=True)

        # # self.channel.start_consuming()

    def shut_down(self) -> None:
        """
            Shuts down the application by stopping the background event loop and disconnecting
            the application from the broker.
        """
        # unregister callback functions
        self.client.message_callback_remove(
            # f"{self.prefix}/{self.manager_app_name}/init"
            f"{self.prefix}.{self.manager_app_name}.init"
        )
        self.client.message_callback_remove(
            # f"{self.prefix}/{self.manager_app_name}/start"
            f"{self.prefix}.{self.manager_app_name}.start"
        )
        self.client.message_callback_remove(
            # f"{self.prefix}/{self.manager_app_name}/stop"
            f"{self.prefix}.{self.manager_app_name}.stop"
        )
        self.client.message_callback_remove(
            # f"{self.prefix}/{self.manager_app_name}/update"
            f"{self.prefix}.{self.manager_app_name}.update"
        )
        # shut down base application
        super().shut_down()

    def on_manager_init(self, ch, method, properties, body) -> None: #, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application to respond to an initilize command sent from the manager.
        Parses the scenario start/end times and signals ready.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object):  private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            logger.info('Manager sent initilize command.')
            message = body.decode('utf-8')
            # message = json.loads(message)
            
            # parse message payload
            # params = InitCommand.parse_raw(message.payload).tasking_parameters
            params = InitCommand.parse_raw(message).tasking_parameters

            # update default execution start/end time
            self._sim_start_time = params.sim_start_time
            self._sim_stop_time = params.sim_stop_time
            self.ready()
            logger.info('App sent ready message.')
        except Exception as e:
            logger.error(
                # f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_start(self, ch, method, properties, body) -> None: #, client: Client, userdata: object, message: MQTTMessage) -> None:
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
            logger.info('Manager sent start command.')
            message = body.decode('utf-8')
            # message = json.loads(message)

            # parse message payload
            # params = StartCommand.parse_raw(message.payload).tasking_parameters
            # logger.info(f"Received start command {message.payload}")
            params = StartCommand.parse_raw(message).tasking_parameters
            logger.info(f"Received start command {message}")

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
                # f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_stop(self, ch, method, properties, body) -> None: #, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application ('self') to respond to a stop command sent from the manager.
        Parses the end time and updates the simulator.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object): private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            logger.info('Manager sent stop command.')
            message = body.decode('utf-8')
            # message = json.loads(message)

            # parse message payload
            # params = StopCommand.parse_raw(message.payload).tasking_parameters
            # logger.info(f"Received stop command {message.payload}")
            params = StopCommand.parse_raw(message).tasking_parameters
            logger.info(f"Received stop command {message}")

            # update execution end time
            self.simulator.set_end_time(params.sim_stop_time)
        except Exception as e:
            logger.error(
                # f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_manager_update(self, ch, method, properties, body) -> None: #, client: Client, userdata: object, message: MQTTMessage) -> None:
        """
        Callback function for the managed application ('self') to respond to an update command sent from the manager.
        Parses the time scaling factor and scenario update time and updates the simulator.

        Args:
            client (:obj:`paho.mqtt.client.Client`): client instance for this callback
            userdata (object): private user data as set in the client
            message (:obj:`paho.mqtt.client.MQTTMessage`): MQTT message
        """
        try:
            logger.info('Manager sent update command.')
            message = body.decode('utf-8')
            # message = json.loads(message)
            
            # parse message payload
            # params = UpdateCommand.parse_raw(message.payload).tasking_parameters
            # logger.info(f"Received update command {message.payload}")
            params = UpdateCommand.parse_raw(message).tasking_parameters
            logger.info(f"Received update command {message}")
            
            # update execution time scale factor
            self.simulator.set_time_scale_factor(
                params.time_scaling_factor, params.sim_update_time
            )
        except Exception as e:
            logger.error(
                # f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())
