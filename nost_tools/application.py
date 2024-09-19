import pika
import threading
import logging
from datetime import datetime, timedelta
from typing import Callable
from keycloak.keycloak_openid import KeycloakOpenID
import getpass
import ssl
from keycloak.exceptions import KeycloakAuthenticationError
import functools
from pika.adapters.asyncio_connection import AsyncioConnection
import time
import ntplib
import sys

import pika.connection

from .schemas import ReadyStatus
from .simulator import Simulator
from .application_utils import (
    ConnectionConfig,
    TimeStatusPublisher,
    ModeStatusObserver,
    ShutDownObserver,
)

logger = logging.getLogger(__name__)

class Application:
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
        self.connection = None
        self.channel = None
        self.prefix = None
        self.app_name = app_name
        self.app_description = app_description
        self._time_status_publisher = None
        self._mode_status_observer = None
        self._shut_down_observer = None
        self._is_connected = threading.Event()
        self._should_stop = threading.Event()
        self.consuming = False
        self.closing = False
        self._is_running = False
        self.io_thread = None

        self.refresh_token = None
        self.token_refresh_thread = None
        self.token_refresh_interval = 180  # seconds

    def ready(self) -> None:
        """
        Signals the application is ready to initialize scenario execution.
        Publishes a :obj:`ReadyStatus` message to the topic `prefix.app_name.status.ready`.
        """
        status = ReadyStatus.parse_obj(
            {
                "name": self.app_name,
                "description": self.app_description,
                "properties": {"ready": True},
            }
        )
        self.send_message(app_name=self.app_name, app_topic='status.ready', payload=status.json(by_alias=True, exclude_none=True))

    def new_access_token(self, config, refresh_token=None):
        """
        Obtains a new access token and refresh token from Keycloak. If a refresh token is provided, the access token is refreshed using the refresh token. Otherwise, the access token is obtained using the username and password provided in the configuration.
        
        Args:
            config (:obj:`ConnectionConfig`): connection configuration
            refresh_token (str): refresh token (optional)
        """
        keycloak_openid = KeycloakOpenID(server_url=f'{'http' if 'localhost' in config.host else 'https'}://{config.host}:{config.keycloak_port}',
                                        client_id=config.client_id,
                                        realm_name=config.keycloak_realm,
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
                except KeycloakAuthenticationError as e:
                    logger.error(f"Authentication error without OTP: {e}")
                    otp = input("Enter OTP: ")
                    token = keycloak_openid.token(grant_type='password', 
                                                username=config.username, 
                                                password=config.password, 
                                                totp=otp)
            if 'access_token' in token:
                logger.info(f"Access token successfully acquired with scopes: {token['scope']}")
                return token['access_token'], token['refresh_token']
            else:
                raise Exception("Error: The request was unsuccessful.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    def start_token_refresh_thread(self, config):
        """
        Starts a background thread to refresh the access token periodically.

        Args:
            config (:obj:`ConnectionConfig`): connection configuration
        """
        def refresh_token_periodically():
            while not self._should_stop.is_set():
                time.sleep(self.token_refresh_interval)
                try:
                    access_token, refresh_token = self.new_access_token(config, self.refresh_token)
                    self.refresh_token = refresh_token
                    self.update_connection_credentials(access_token)
                    logger.info("Access token refreshed successfully.")
                except Exception as e:
                    logger.error(f"Failed to refresh access token: {e}")

        self.token_refresh_thread = threading.Thread(target=refresh_token_periodically)
        self.token_refresh_thread.start()

    def update_connection_credentials(self, access_token):
        """
        Updates the connection credentials with the new access token.

        Args:
            access_token (str): new access token
        """
        self.connection.update_secret(access_token, 'secret')
        # self.connection._credentials = pika.PlainCredentials('', access_token)
        # self.connection._adapter_disconnect()

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = True,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = False,
    ) -> None:
        """
        Starts up the application to prepare for scenario execution.
        Connects to the message broker and starts a background event loop by establishing the simulation prefix,
        the connection configuration, and the intervals for publishing time status messages.

        Args:
            prefix (str): messaging namespace (prefix)
            config (:obj:`ConnectionConfig`): connection configuration
            set_offset (bool): True, if the system clock offset shall be set using a NTP request prior to execution
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time for first time status message
            shut_down_when_terminated (bool): True, if the application should shut down when the simulation is terminated
        """
        if set_offset:
            self.set_wallclock_offset()
        self.prefix = prefix
        self._is_running = True
        # Obtain access token and refresh token
        access_token, refresh_token = self.new_access_token(config)
        self.start_token_refresh_thread(config)

        # # Set up connection parameters
        # if config.is_tls:
        #     ssl_options = pika.SSLOptions(ssl.create_default_context(), config.host)
        #     parameters = pika.ConnectionParameters(
        #         host=config.host,
        #         virtual_host=config.virtual_host,
        #         port=config.rabbitmq_port,
        #         credentials=pika.PlainCredentials('', access_token),
        #         heartbeat=600,
        #         ssl_options=ssl_options
        #     )
        # else:
        #     parameters = pika.ConnectionParameters(
        #         host=config.host,
        #         virtual_host=config.virtual_host,
        #         port=config.rabbitmq_port,
        #         credentials=pika.PlainCredentials('', access_token),
        #         heartbeat=600
        #     )

        # Set up connection parameters
        parameters = pika.ConnectionParameters(
            host=config.host,
            virtual_host=config.virtual_host,
            port=config.rabbitmq_port,
            credentials=pika.PlainCredentials('', access_token),
            heartbeat=600
        )

        # Configure transport layer security (TLS) if needed
        if config.is_tls:
            logger.info("Using TLS/SSL.")
            context = ssl.create_default_context()
            parameters.ssl_options = pika.SSLOptions(context)
            
        def on_connection_open(connection):
            self.connection = connection
            self.connection.channel(on_open_callback=self.on_channel_open)
            logger.info("Connection established successfully.")
        self.connection = pika.SelectConnection(
            parameters=parameters,
            on_open_callback=on_connection_open,
            on_open_error_callback=self.on_connection_error,
            on_close_callback=self.on_connection_closed,
        )
        # Start the I/O loop in a separate thread
        # threading.Thread(target=self._start_io_loop).start()
        # self._is_connected.wait()
        self.stop_event = threading.Event()
        self.io_thread = threading.Thread(target=self._start_io_loop)
        self.io_thread.start()
        self._is_connected.wait()
        
        # Configure observers
        self._create_time_status_publisher(time_status_step, time_status_init)
        self._create_mode_status_observer()
        if shut_down_when_terminated:
            self._create_shut_down_observer()
        logger.info(f"Application {self.app_name} successfully started up.")

    def _start_io_loop(self):
        """
        Starts the I/O loop for the connection.
        """
        self.stop_event = threading.Event()

        # while self._is_running:
        while not self.stop_event.is_set():
            self.connection.ioloop.start()

    def on_channel_open(self, channel):
        """
        Callback function for when the channel is opened.
        
        Args:
            channel (:obj:`pika.channel.Channel`): channel object
        """
        self.channel = channel
        # Signal that connection is established
        self._is_connected.set()

    def on_connection_error(self, connection, error):
        """
        Callback function for when a connection error occurs.

        Args:
            connection (:obj:`pika.connection.Connection`): connection object
            error (Exception): exception representing reason for loss of connection
        """
        logger.error(f"Connection error: {error}")
        self._is_connected.clear()

    def on_connection_closed(self, connection, reason):
        """
        This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        Args:
            connection (:obj:`pika.connection.Connection`): closed connection object
            reason (Exception): exception representing reason for loss of connection
        """
        self.channel = None
        if self.closing:
            self.connection.ioloop.stop()

    def shut_down(self) -> None:
        """
        Shuts down the application by stopping the background event loop and disconnecting from the broker.
        """
        self._should_stop.set()
        if self._time_status_publisher is not None:
            self.simulator.remove_observer(self._time_status_publisher)
        self._time_status_publisher = None

        if self.connection:
            self.stop_application()
            self.consuming = False
        
        logger.info(f"Application {self.app_name} successfully shut down.")

    def send_message(self, app_name, app_topic: str, payload: str, app_specific_extender: str = None) -> None:
        """
        Sends a message to the broker. The message is sent to the exchange using the routing key. The routing key is created using the application name and topic. The message is published with an expiration of 60 seconds.
        
        Args:
            app_name (str): application name
            app_topic (str): topic name
            payload (str): message payload
            app_specific_extender (str): application specific extender, used to create a unique queue name for the application. If the app_specific_extender is not provided, the queue name is the same as the routing key.
        """
        if app_specific_extender:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic, app_specific_extender=app_specific_extender)
        else:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic)
        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=routing_key,
            body=payload,
            properties=pika.BasicProperties(expiration='30000')
        )
        logger.debug(f'Successfully sent message "{payload}" to topic "{routing_key}".')

    def add_message_callback(self, app_name: str, app_topic: str, user_callback: Callable, app_specific_extender: str = None):
        """
        This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.
        """
        self.was_consuming = True
        self.consuming = True
        logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        combined_cb = self.combined_callback(user_callback)
        if app_specific_extender:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic, app_specific_extender=app_specific_extender)
        else:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic)
        # Set QoS settings
        self.channel.basic_qos(prefetch_count=1)
        self._consumer_tag = self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=combined_cb,
            auto_ack=False)
        logger.info(f"Subscribing and adding callback to topic: {routing_key}")

    def combined_callback(self, user_callback):
        def wrapper(ch, method, properties, body):
            # Call the on_message method
            self.on_message(ch, method, properties, body)
            # Call the user-provided callback
            user_callback(ch, method, properties, body)
        return wrapper

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.
        """
        logger.info('Adding consumer cancellation callback')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        logger.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        self.channel.close()

    def on_message(self, ch, method, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel _unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param bytes body: The message body
        """
        logger.debug(f'Received message # {method.delivery_tag}: {body.decode('utf8')}')
        self.acknowledge_message(method.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        try:
            logger.debug(f'Acknowledging message {delivery_tag}')
            self.channel.basic_ack(delivery_tag, True)
        except:
            pass

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self.channel:
            logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(
                self.on_cancelok, userdata=self._consumer_tag)
            self.channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.
        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)
        """
        self.consuming = False
        logger.info(
            'RabbitMQ acknowledged the cancellation of the consumer: %s',
            userdata)
        self.close_channel()
        self.stop_loop()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.
        """
        logger.info('Closing channel')
        self.channel.close()

    def stop_loop(self):
        """Stop the IO loop
        """
        self.connection.ioloop.stop()

    def stop_application(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.
        """
        if not self.closing:
            self.closing = True
            if self.consuming:
                self.stop_consuming()
                # Signal the thread to stop
                if hasattr(self, 'stop_event'):
                    self.stop_event.set()
                if hasattr(self, 'io_thread'):
                    self.io_thread.join()
                sys.exit()
            else:
                self.connection.ioloop.stop()

    def remove_message_callback(self):
        """This method cancels the consumer by issuing the Basic.Cancel RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. It also ensures that the consumer is no longer
        consuming messages.
        """
        if self._consumer_tag:
            logger.info('Cancelling the consumer')
            self.stop_application()
            self._consumer_tag = None
            self.was_consuming = False
            self.consuming = False
            logger.debug('Consumer cancelled successfully')
        else:
            logger.warning('No consumer to cancel')

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

    def _create_time_status_publisher(self, time_status_step: timedelta, time_status_init: datetime) -> None:
        """
        Creates a new time status publisher to publish the time status when it changes.

        Args:
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time for first time status message
        """
        if time_status_step is not None:
            if self._time_status_publisher is not None:
                self.simulator.remove_observer(self._time_status_publisher)
            self._time_status_publisher = TimeStatusPublisher(self, time_status_step, time_status_init)
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

    def create_routing_key(self, app_name: str, topic: str):
        """
        Creates a routing key for the application. The routing key is used to bind the queue to the exchange.

        Args:
            app_name (str): application name
            topic (str): topic name
        """
        routing_key = '.'.join([self.prefix, app_name, topic])
        return routing_key

    def declare_bind_queue(self, app_name: str, topic: str, app_specific_extender: str = None) -> None:
        """
        Declares and binds a queue to the exchange. The queue is bound to the exchange using the routing key. The routing key is created using the application name and topic.
        Args:
            app_name (str): application name
            topic (str): topic name 
            app_specific_extender (str): application specific extender, used to create a unique queue name for the application. If the app_specific_extender is not provided, the queue name is the same as the routing key.
        """
        try:

            self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic', durable=True)
            routing_key = self.create_routing_key(app_name=app_name, topic=topic)
            if app_specific_extender:
                queue_name = '.'.join([routing_key, app_specific_extender])
            else:
                queue_name = routing_key
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=routing_key)
            logger.debug(f'Bound queue "{queue_name}" to topic "{routing_key}".')
        
        except:
            routing_key = None
            queue_name = None
            pass

        return routing_key, queue_name