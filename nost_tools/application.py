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

    def __init__(self, app_name: str, config: ConnectionConfig, app_description: str = None): #, 
        """
        Initializes a new application.

        Args:
            app_name (str): application name
            app_description (str): application description (optional)
        """
        self.simulator = Simulator()
        # self.client = mqtt.Client()
        # self.client = pika.BlockingConnection().channel()
        # self.client = pika.BlockingConnection(pika.ConnectionParameters('localhost')).channel()
        self.prefix = None
        self.app_name = app_name
        self.app_description = app_description
        self._time_status_publisher = None
        self._mode_status_observer = None
        self._shut_down_observer = None

        # Obtain access token and refresh token
        access_token, refresh_token = self.new_access_token(config)

        # Set up connection parameters
        parameters = pika.ConnectionParameters(
            host=config.host,
            virtual_host=config.virtual_host,
            port=config.rabbitmq_port,
            credentials=pika.PlainCredentials('', access_token)
        )

        # Configure transport layer security (TLS) if needed
        if config.is_tls:
            logger.info("Using TLS/SSL.")
            context = ssl.create_default_context()
            parameters.ssl_options = pika.SSLOptions(context)

        # Connect to server
        try:
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connection established successfully.")
        except pika.exceptions.ProbableAccessDeniedError as e:
            logger.info(f"Access denied: {e}")
            sys.exit(1)

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
        
        # Push to start_up()
        topic = f"{self.prefix}.{self.app_name}.status.ready"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 
        ###

        # Declare the topic exchange
        # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')
        
        # Declare a queue and bind it to the exchange with the routing key
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)

        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=topic,
            body=status.json(by_alias=True, exclude_none=True),
            properties=pika.BasicProperties(expiration='30000')
        )
        
        logger.info(f'Application "{self.app_name}" successfully sent ready message.')

    def new_access_token(self, config, refresh_token=None):

        keycloak_openid = KeycloakOpenID(server_url=f'{'http' if 'localhost' in config.host else 'https'}://{config.host}:{config.keycloak_port}', #"http://localhost:8080/",
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

        # Declare the topic exchange
        self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')
        
        # access_token, refresh_token = self.new_access_token(config)
        # parameters = pika.ConnectionParameters(
        #         host=config.host,
        #         virtual_host=config.virtual_host,
        #         port=config.rabbitmq_port,
        #         credentials=pika.PlainCredentials('', access_token))

        # # Configure transport layer security (TLS) if needed
        # if config.is_tls:
        #     logger.info("Using TLS/SSL.")
        #     context = ssl.create_default_context()
        #     parameters.ssl_options = pika.SSLOptions(context)

        # # Connect to server
        # try:
        #     self.connection = pika.BlockingConnection(parameters)
        #     logger.info("Connection established successfully.")
        # except pika.exceptions.ProbableAccessDeniedError as e:
        #     logger.info(f"Access denied: {e}")
        #     sys.exit(1)

        # self.channel = self.connection.channel()

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
        
        # close the connection
        # if self.client.is_open:
        #     self.client.close()
        if self.channel.is_open:
            self.channel.close()
        
        if self.channel.is_closed:
            # clear prefix
            # self.prefix = None
            logger.info(f'Application "{self.app_name}" successfully shut down.')

    def send_message(self, app_topic: str, payload: str) -> None:
        """
        Sends a message with payload `payload` to the topic `prefix/app_name/app_topic`.

        Args:
            app_topic (str): application topic
            payload (str): message payload (JSON-encoded string)

        """
        
        # Part of start_up(): Define all queues that should be declared (time.status, .ready, etc.)
        # Take one position or other declared in advance or latest possible moment (choose one, I will decide which makes more sense based on users [easier to use may be preferred by users])
        topic = f"{self.prefix}.{self.app_name}.{app_topic}"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        # Declare a queue and bind it to the exchange with the routing key
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic) #f"{self.prefix}.{self.app_name}.status.time")

        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=topic,
            # routing_key=f"{self.prefix}.{self.app_name}.status.time",
            body=payload,
            properties=pika.BasicProperties(expiration='30000')
        )

        logger.info(f"Successfully sent message {topic}: {payload}")

    def add_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:
        """
        Adds a message callback for application name and topic `prefix.app_name.app_topic`.

        Args:
            app_name (str): The application name
            app_topic (str): The application topic
            callback (Callable): The callback function to handle messages
        """
        topic = f"{self.prefix}.{app_name}.{app_topic}"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 


        # Can manager miss messages becuase other apps are subscribing to topic meant for manager
        # Specific destination (auto ack, or not)
        # Quality 
        # Send_message(): Set up the queue
        # print(f'Queue: {queue_name}')
        logger.info(f"Subscribing and adding callback to topic: {topic}")
        
        # Declare the exchange
        # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # # Declare the queue, 60000 milliseconds = 60 seconds 
        self.channel.queue_declare(queue=queue_name, durable=True) #, arguments={'x-message-ttl': 60000})
        
        # Bind the queue to the exchange with the routing key
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)
        
        # Set QoS settings
        self.channel.basic_qos(prefetch_count=1)

        # Consume messages from the queue
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False) #True)

        ## Set expiry period: at queue or publishing? (max amount of time before being removed, would be important)

    def remove_message_callback(self, app_name: str, app_topic: str) -> None:
        """
        Removes a message callback for application name and topic `prefix.app_name.app_topic`.

        Args:
            app_name (str): The application name
            app_topic (str): The application topic
        """
        self.channel.stop_consuming()

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
