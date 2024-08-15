"""
Provides a base application that publishes messages from a simulator to a broker.
"""

from datetime import datetime, timedelta
import logging
import ntplib
import paho.mqtt.client as mqtt
import time
from typing import Callable

import pika
from datetime import timedelta, datetime
import requests
import sys
from keycloak.keycloak_openid import KeycloakOpenID
import getpass
import ssl
from keycloak.exceptions import KeycloakAuthenticationError

from .schemas import ReadyStatus
from .simulator import Simulator
from .application_utils import (
    ConnectionConfig,
    TimeStatusPublisher,
    ModeStatusObserver,
    ShutDownObserver,
)

logger = logging.getLogger(__name__)


class Application(object):
    """
    Base class for a member application.

    This object class defines the main functionality of a NOS-T application which can be modified for user needs.

    Attributes:
        prefix (str): The test run namespace (prefix)
        simulator (:obj:`Simulator`): Application simulator -- calls on the simulator.py class for functionality
        client (:obj:`Client`): Application MQTT client
        app_name (str): Test run application name
        app_description (str): Test run application description (optional)
        time_status_step (:obj:`timedelta`): Scenario duration between time status messages
        time_status_init (:obj:`datetime`): Scenario time of first time status message
    """

    def __init__(self, app_name: str, app_description: str = None):
        """
        Initializes a new application.

        Args:
            app_name (str): application name
            app_description (str): application description (optional)
        """
        self.simulator = Simulator()
        self.client = mqtt.Client()
        # self.client = pika.BlockingConnection(pika.ConnectionParameters('localhost')).channel()
        self.prefix = None
        self.app_name = app_name
        self.app_description = app_description
        self._time_status_publisher = None
        self._mode_status_observer = None
        self._shut_down_observer = None

    def ready(self) -> None:
        """
        Signals the application is ready to initialize scenario execution.
        Publishes a :obj:`ReadyStatus` message to the topic `prefix/app_name/status/ready`.
        """
        # publish ready status message
        status = ReadyStatus.parse_obj(
            {
                "name": self.app_name,
                "description": self.app_description,
                "properties": {"ready": True},
            }
        )
        
        # self.client.publish(
        #     f"{self.prefix}/{self.app_name}/status/ready",
        #     status.json(by_alias=True, exclude_none=True),
        # )
        
        # Declare the topic exchange
        self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # Declare a queue and bind it to the exchange with the routing key
        topic = f"{self.prefix}.{self.app_name}.status.time"
        # queue_name = f"{topic}.queue"
        # queue_name = "_".join(topic.split(".")) + "_queue"
        queue_name = ".".join(topic.split(".") + ["queue"]) 

        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)

        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=topic,
            body=status.json(by_alias=True, exclude_none=True)
        )
        logger.info(
            f"Successfully sent time status {status.json(by_alias=True,exclude_none=True)}."
        )

    def new_access_token(self, config, refresh_token=None):
        keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
                                        client_id=config.client_id,
                                        realm_name="test",
                                        client_secret_key=config.client_secret_key
                                        )

        try:
            if refresh_token:
                token = keycloak_openid.refresh_token(refresh_token)
            else:
                # Attempt to get token without OTP
                try:
                    token = keycloak_openid.token(grant_type='password', 
                                                username=config.username, 
                                                password=config.password)
                                                # scope='openid rabbitmq.read:*/nost/nost.* rabbitmq.write:*/nost/nost.* rabbitmq.configure:*/nost/nost.*')
                except KeycloakAuthenticationError as e:

                    logger.error(f"Authentication error without OTP: {e}")
                    otp = input("Enter OTP: ")
                    token = keycloak_openid.token(grant_type='password', 
                                                username=config.username, 
                                                password=config.password, 
                                                totp=otp)
                                                # scope='openid rabbitmq.read:*/nost/nost.* rabbitmq.write:*/nost/nost.* rabbitmq.configure:*/nost/nost.*')

            if 'access_token' in token:
                logger.info("Access token successfully acquired.")
                logger.info(f"Access token scopes: {token["scope"]}")
                return token['access_token'], token['refresh_token']
            else:
                raise Exception("Error: The request was unsuccessful.")
            
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    # def start_up(
    #     self,
    #     prefix: str,
    #     config: ConnectionConfig,
    #     set_offset: bool = True,
    #     time_status_step: timedelta = None,
    #     time_status_init: datetime = None,
    #     shut_down_when_terminated: bool = False,
    # ) -> None:
    #     """
    #     Starts up the application to prepare for scenario execution.
    #     Connects to the message broker and starts a background event loop by establishing the simulation prefix,
    #     the connection configuration, and the intervals for publishing time status messages.

    #     Args:
    #         prefix (str): messaging namespace (prefix)
    #         config (:obj:`ConnectionConfig`): connection configuration
    #         set_offset (bool): True, if the system clock offset shall be set using a NTP request prior to execution
    #         time_status_step (:obj:`timedelta`): scenario duration between time status messages
    #         time_status_init (:obj:`datetime`): scenario time for first time status message
    #         shut_down_when_terminated (bool): True, if the application should shut down when the simulation is terminated
    #     """
    #     # Maybe configure wallclock offset
    #     if set_offset:
    #         self.set_wallclock_offset()

    #     # Set test run prefix
    #     self.prefix = prefix

    #     # global otp
    #     # otp = input("Enter OTP: ")

    #     access_token, refresh_token = self.new_access_token(config)
    #     parameters = pika.ConnectionParameters(
    #             host=config.host,
    #             virtual_host=config.virtual_host,
    #             port=config.port,
    #             # ssl_options=pika.SSLOptions() if config.is_tls else None,
    #             credentials=pika.PlainCredentials('', access_token))

    #     # Configure transport layer security (TLS) if needed
    #     if config.is_tls:
    #         logger.info("Using TLS/SSL.")
    #         context = ssl.create_default_context()
    #         parameters.ssl_options = pika.SSLOptions(context)

    #     # Connect to server
    #     try:
    #         self.connection = pika.BlockingConnection(parameters)
    #         logger.info("Connection established successfully.")
    #     except pika.exceptions.ProbableAccessDeniedError as e:
    #         logger.info(f"Access denied: {e}")
    #         sys.exit(1)

    #     self.channel = self.connection.channel()

    #     # Configure observers
    #     self._create_time_status_publisher(time_status_step, time_status_init)
    #     self._create_mode_status_observer()
    #     if shut_down_when_terminated:
    #         self._create_shut_down_observer()

    #     logger.info(f"Application {self.app_name} successfully started up.")

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = True,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = False,
    ) -> None:
        # Maybe configure wallclock offset
        if set_offset:
            self.set_wallclock_offset()

        # Set test run prefix
        self.prefix = prefix

        access_token, refresh_token = self.new_access_token(config)
        parameters = pika.ConnectionParameters(
                host=config.host,
                virtual_host=config.virtual_host,
                port=config.port,
                credentials=pika.PlainCredentials('', access_token))

        # Configure transport layer security (TLS) if needed
        if config.is_tls:
            logger.info("Using TLS/SSL.")
            context = ssl.create_default_context()
            parameters.ssl_options = pika.SSLOptions(context)

        # Connect to server
        try:
            self.connection = pika.BlockingConnection(parameters)
            logger.info("Connection established successfully.")
        except pika.exceptions.ProbableAccessDeniedError as e:
            logger.info(f"Access denied: {e}")
            sys.exit(1)

        self.channel = self.connection.channel()

        # Configure observers
        self._create_time_status_publisher(time_status_step, time_status_init)
        self._create_mode_status_observer()
        if shut_down_when_terminated:
            self._create_shut_down_observer()

        logger.info(f'Application "{self.app_name}" successfully started up.')

    def _create_time_status_publisher(
        self, time_status_step: timedelta, time_status_init: datetime
    ) -> None:
        """
        Creates a new time status publisher to publish the time status when it changes.

        Args:
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time for first time status message
        """
        if time_status_step is not None:
            if self._time_status_publisher is not None:
                self.simulator.remove_observer(self._time_status_publisher)
            self._time_status_publisher = TimeStatusPublisher(
                self, time_status_step, time_status_init
            )
            self.simulator.add_observer(self._time_status_publisher)

    def _create_mode_status_observer(self) -> None:
        """
        Creates a mode status observer to publish the mode status when it changes.
        """
        if self._mode_status_observer is not None:
            self.simulator.remove_observer(self._mode_status_observer)
        self._mode_status_observer = ModeStatusObserver(self)
        self.simulator.add_observer(self._mode_status_observer)

    def _create_shut_down_observer(self) -> None:
        """
        Creates an observer to shut down the application when the simulation is terminated.
        """
        if self._shut_down_observer is not None:
            self.simulator.remove_observer(self._shut_down_observer)
        self._shut_down_observer = ShutDownObserver(self)
        self.simulator.add_observer(self._shut_down_observer)

    def shut_down(self) -> None:
        """
        Shuts down the application by stopping the background event loop and disconnecting from the broker.
        """
        if self._time_status_publisher is not None:
            # remove the time status observer
            self.simulator.remove_observer(self._time_status_publisher)
        self._time_status_publisher = None
        # stop background loop
        self.client.loop_stop()
        # disconnect form server
        self.client.disconnect()
        # clear prefix
        self.prefix = None
        logger.info(f"Application {self.app_name} successfully shut down.")

    def send_message(self, app_topic: str, payload: str) -> None:
        """
        Sends a message with payload `payload` to the topic `prefix/app_name/app_topic`.

        Args:
            app_topic (str): application topic
            payload (str): message payload (JSON-encoded string)

        """
        topic = f"{self.prefix}.{self.app_name}.{app_topic}"
        # queue_name = f"{topic}.queue"
        # queue_name = "_".join(topic.split(".")) + "_queue"
        queue_name = ".".join(topic.split(".") + ["queue"]) 

        logger.info(f"Publishing to topic {topic}: {payload}")
        # self.client.publish(topic, payload)
        
        # Declare a queue and bind it to the exchange with the routing key
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic) #f"{self.prefix}.{self.app_name}.status.time")

        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=topic,
            # routing_key=f"{self.prefix}.{self.app_name}.status.time",
            body=payload
        )

    # def add_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:
    #     topic = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.debug(f"Subscribing and adding callback to topic: {topic}")
    #     self.channel.queue_bind(exchange=self.prefix, queue=self.prefix, routing_key=topic)
    #     self.channel.basic_consume(queue=topic, on_message_callback=callback, auto_ack=True)

    # def add_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:
    #     """
    #     Adds a message callback for application name and topic `prefix.app_name.app_topic`.

    #     Args:
    #         app_name (str): The application name
    #         app_topic (str): The application topic
    #         callback (Callable): The callback function to handle messages
    #     """
    #     topic = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.info(f"Subscribing and adding callback to topic: {topic}")
        
    #     # Declare the exchange
    #     self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

    #     # Declare the queue
    #     self.channel.queue_declare(queue=self.prefix, durable=True)
        
    #     # Bind the queue to the exchange with the routing key
    #     self.channel.queue_bind(exchange=self.prefix, queue=self.prefix, routing_key=topic)
        
    #     # Consume messages from the queue
    #     self.channel.basic_consume(queue=self.prefix, on_message_callback=callback, auto_ack=True)

    #     # Start consuming
    #     # self.channel.start_consuming()

    def add_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:
        """
        Adds a message callback for application name and topic `prefix.app_name.app_topic`.

        Args:
            app_name (str): The application name
            app_topic (str): The application topic
            callback (Callable): The callback function to handle messages
        """
        topic = f"{self.prefix}.{app_name}.{app_topic}"
        # queue_name = f"{topic}.queue"
        # queue_name = "_".join(topic.split(".")) + "_queue"
        queue_name = ".".join(topic.split(".") + ["queue"]) 

        print(f'Queue: {queue_name}')
        logger.info(f"Subscribing and adding callback to topic: {topic}")
        
        # Declare the exchange
        self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # # Declare the queue
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind the queue to the exchange with the routing key
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)
        
        # Consume messages from the queue
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)



    # def remove_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:

    #     topic = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.debug(f"Removing callback from topic: {topic}")

    #     # Unbind the queue
    #     # self.channel.queue_bind(exchange=self.prefix, queue=self.prefix, routing_key=topic)
    #     self.channel.queue_unbind(queue=self.prefix, exchange=self.prefix, routing_key=topic)

    def remove_message_callback(self, app_name: str, app_topic: str) -> None:
        """
        Removes a message callback for application name and topic `prefix.app_name.app_topic`.

        Args:
            app_name (str): The application name
            app_topic (str): The application topic
        """
        topic = f"{self.prefix}.{app_name}.{app_topic}"
        queue_name = ".".join(topic.split(".") + ["queue"])

        print(f'Removing callback from queue: {queue_name}')
        logger.info(f"Unsubscribing and removing callback from topic: {topic}")

        # Cancel the consumer
        self.channel.basic_cancel(consumer_tag=queue_name)

        # Unbind the queue from the exchange
        self.channel.queue_unbind(exchange=self.prefix, queue=queue_name, routing_key=topic)

        # Delete the queue
        self.channel.queue_delete(queue=queue_name)

    # def add_message_callback(
    #     self, app_name: str, app_topic: str, callback: Callable
    # ) -> None:
    #     """
    #     Adds a message callback bound to an application name and topic `prefix/app_name/app_topic`.

    #     Args:
    #         app_name (str): application name
    #         app_topic (str): application topic
    #         callback (Callable): callback function
    #     """
    #     # topic = f"{self.prefix}/{app_name}/{app_topic}"
    #     # logger.debug(f"Subscribing and adding callback to topic: {topic}")
    #     # self.client.subscribe(topic)
    #     # self.client.message_callback_add(topic, callback)
    #     topic = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.debug(f"Subscribing and adding callback to topic: {topic}")
    #     self.channel.basic_consume(queue=self.prefix, on_message_callback=callback, auto_ack=True)
    #     self.channel.add_on_return_callback(callback=callback)

    # def remove_message_callback(self, app_name: str, app_topic: str) -> None:
    #     """
    #     Removes a message callback for application name and topic `prefix/app_name/app_topic`.

    #     Args:
    #         app_name (str): The application name
    #         app_topic (str): The application topic
    #     """
    #     # topic = f"{self.prefix}/{app_name}/{app_topic}"
    #     # logger.debug(f"Removing callback from topic: {topic}")
    #     # self.client.message_callback_remove(topic)
    #     topic = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.debug(f"Subscribing and adding callback to topic: {topic}")

    def set_wallclock_offset(
        self, host="pool.ntp.org", retry_delay_s: int = 5, max_retry: int = 5
    ) -> None:
        """
        Issues a Network Time Protocol (NTP) request to determine the system clock offset.

        Args:
            host (str): NTP host (default: 'pool.ntp.org')
            retry_delay_s (int): number of seconds to wait before retrying
            max_retry (int): maximum number of retries allowed
        """
        for i in range(max_retry):
            try:
                logger.info(f"Contacting {host} to retrieve wallclock offset.")
                response = ntplib.NTPClient().request(host, version=3, timeout=2)
                offset = timedelta(seconds=response.offset)
                self.simulator.set_wallclock_offset(offset)
                logger.info(f"Wallclock offset updated to {offset}.")
                return
            except ntplib.NTPException:
                logger.warn(
                    f"Could not connect to {host}, attempt #{i+1}/{max_retry} in {retry_delay_s} s."
                )
                time.sleep(retry_delay_s)
