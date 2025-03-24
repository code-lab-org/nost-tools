"""
Provides a base application that publishes messages from a simulator to a broker.
"""

import functools
import logging
import ssl
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Callable

import ntplib
import pika
import pika.connection
import urllib3
from keycloak.exceptions import KeycloakAuthenticationError
from keycloak.keycloak_openid import KeycloakOpenID

from .application_utils import (  # ConnectionConfig,
    ModeStatusObserver,
    ShutDownObserver,
    TimeStatusPublisher,
)
from .configuration import ConnectionConfig
from .schemas import ReadyStatus
from .simulator import Simulator

logging.captureWarnings(True)
logger = logging.getLogger(__name__)
urllib3.disable_warnings()


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
        self.config = None
        # Connection status
        self._is_connected = threading.Event()
        self._is_running = False
        self._io_thread = None
        self._consuming = False
        self._should_stop = threading.Event()
        self._closing = False
        # Queues
        self.channel_configs = []
        self.unique_exchanges = {}
        self.declared_queues = set()
        self.declared_exchanges = set()
        self.predefined_exchanges_queues = False
        self._callbacks_per_topic = {}
        # Token
        self.refresh_token = None
        self._token_refresh_thread = None
        self.token_refresh_interval = None

    def ready(self) -> None:
        """
        Signals the application is ready to initialize scenario execution.
        Publishes a :obj:`ReadyStatus` message to the topic `prefix.app_name.status.ready`.
        """
        status = ReadyStatus.model_validate(
            {
                "name": self.app_name,
                "description": self.app_description,
                "properties": {"ready": True},
            }
        )
        self.send_message(
            app_name=self.app_name,
            app_topics="status.ready",
            payload=status.model_dump_json(by_alias=True, exclude_none=True),
        )

    def new_access_token(self, refresh_token=None):
        """
        Obtains a new access token and refresh token from Keycloak. If a refresh token is provided,
        the access token is refreshed using the refresh token. Otherwise, the access token is obtained
        using the username and password provided in the configuration.

        Args:
            refresh_token (str): refresh token (optional)
        """
        logger.debug(
            "Acquiring access token."
            if not refresh_token
            else "Refreshing access token."
        )
        keycloak_openid = KeycloakOpenID(
            server_url=f"{'http' if 'localhost' in self.config.rc.server_configuration.servers.keycloak.host or '127.0.0.1' in self.config.rc.server_configuration.servers.keycloak.host else 'https'}://{self.config.rc.server_configuration.servers.keycloak.host}:{self.config.rc.server_configuration.servers.keycloak.port}",
            client_id=self.config.rc.credentials.client_id,
            realm_name=self.config.rc.server_configuration.servers.keycloak.realm,
            client_secret_key=self.config.rc.credentials.client_secret_key,
            verify=False,
        )
        try:
            if refresh_token:
                token = keycloak_openid.refresh_token(refresh_token)
            else:
                try:
                    token = keycloak_openid.token(
                        grant_type="password",
                        username=self.config.rc.credentials.username,
                        password=self.config.rc.credentials.password,
                    )
                except KeycloakAuthenticationError as e:
                    logger.error(f"Authentication error without OTP: {e}")
                    otp = input("Enter OTP: ")
                    token = keycloak_openid.token(
                        grant_type="password",
                        username=self.config.rc.credentials.username,
                        password=self.config.rc.credentials.password,
                        totp=otp,
                    )
            if "access_token" in token:
                logger.debug(
                    "Acquiring access token successfully completed."
                    if not refresh_token
                    else "Refreshing access token successfully completed."
                )
                return token["access_token"], token["refresh_token"]
            else:
                raise Exception("Error: The request was unsuccessful.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    def start_token_refresh_thread(self):
        """
        Starts a background thread to refresh the access token periodically.

        Args:
            config (:obj:`ConnectionConfig`): connection configuration
        """
        logger.debug("Starting refresh token thread.")

        def refresh_token_periodically():
            while not self._should_stop.wait(timeout=self.token_refresh_interval):
                try:
                    access_token, refresh_token = self.new_access_token(
                        self.refresh_token
                    )
                    self.refresh_token = refresh_token
                    self.update_connection_credentials(access_token)
                except Exception as e:
                    logger.error(f"Failed to refresh access token: {e}")

        self._token_refresh_thread = threading.Thread(target=refresh_token_periodically)
        self._token_refresh_thread.start()
        logger.debug("Starting refresh token thread successfully completed.")

    def update_connection_credentials(self, access_token):
        """
        Updates the connection credentials with the new access token.

        Args:
            access_token (str): new access token
        """
        self.connection.update_secret(access_token, "secret")

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = None,  # True,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = None,
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
        if (
            set_offset is not None
            and time_status_step is not None
            and time_status_init is not None
            and shut_down_when_terminated is not None
        ):
            self.set_offset = set_offset
            self.time_status_step = time_status_step
            self.time_status_init = time_status_init
            self.shut_down_when_terminated = shut_down_when_terminated
        else:
            self.config = config
            parameters = getattr(
                self.config.rc.simulation_configuration.execution_parameters,
                self.app_name,
                None,
            )
            self.set_offset = parameters.set_offset
            self.time_status_step = parameters.time_status_step
            self.time_status_init = parameters.time_status_init
            self.shut_down_when_terminated = parameters.shut_down_when_terminated

        if self.set_offset:
            # Set the system clock offset
            self.set_wallclock_offset()

        # Set the prefix and configuration parameters
        self.prefix = prefix
        self.config = config
        self._is_running = True

        if self.config.rc.server_configuration.servers.rabbitmq.keycloak_authentication:
            # Get the access token and refresh token
            self.token_refresh_interval = (
                self.config.rc.server_configuration.servers.keycloak.token_refresh_interval
            )
            logger.info(
                f"Keycloak authentication is enabled. Access token will be refreshed every {self.token_refresh_interval} seconds"
            )
            access_token, _ = self.new_access_token()
            self.start_token_refresh_thread()
            credentials = pika.PlainCredentials("", access_token)
        else:
            # Set up credentials
            credentials = pika.PlainCredentials(
                self.config.rc.credentials.username,
                self.config.rc.credentials.password,
            )

        # Set up connection parameters
        parameters = pika.ConnectionParameters(
            host=self.config.rc.server_configuration.servers.rabbitmq.host,
            virtual_host=self.config.rc.server_configuration.servers.rabbitmq.virtual_host,
            port=self.config.rc.server_configuration.servers.rabbitmq.port,
            credentials=credentials,
            heartbeat=config.rc.server_configuration.servers.rabbitmq.heartbeat,
            connection_attempts=config.rc.server_configuration.servers.rabbitmq.connection_attempts,
            retry_delay=config.rc.server_configuration.servers.rabbitmq.retry_delay,
        )

        # Configure transport layer security (TLS) if needed
        if self.config.rc.server_configuration.servers.rabbitmq.tls:
            logger.info("Using TLS/SSL.")
            parameters.ssl_options = pika.SSLOptions(ssl.SSLContext())

        # Callback functions for connection
        def on_connection_open(connection):
            self.connection = connection
            self.connection.channel(on_open_callback=self.on_channel_open)
            logger.info("Connection established successfully.")

        # Establish non-blocking connection to RabbitMQ
        self.connection = pika.SelectConnection(
            parameters=parameters,
            on_open_callback=on_connection_open,
            on_open_error_callback=self.on_connection_error,
            on_close_callback=self.on_connection_closed,
        )

        # Start the I/O loop in a separate thread
        self._io_thread = threading.Thread(target=self._start_io_loop)
        self._io_thread.start()
        self._is_connected.wait()

        if self.config.rc.simulation_configuration.predefined_exchanges_queues:
            # Get the unique exchanges and channel configurations
            self.predefined_exchanges_queues = True
            logger.debug(
                "Exchanges and queues are predefined in the YAML configuration file."
            )
            self.unique_exchanges, self.channel_configs = (
                self.config.rc.simulation_configuration.exchanges,
                self.config.rc.simulation_configuration.queues,
            )

        else:
            logger.debug(
                "Exchanges and queues are NOT predefined in the YAML configuration file."
            )

        # Configure observers
        self._create_time_status_publisher(self.time_status_step, self.time_status_init)
        self._create_mode_status_observer()
        if self.shut_down_when_terminated:
            self._create_shut_down_observer()
        logger.info(f"Application {self.app_name} successfully started up.")

    def _start_io_loop(self):
        """
        Starts the I/O loop for the connection.
        """
        self.stop_event = threading.Event()
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
        if self._closing:
            self.connection.ioloop.stop()

    def shut_down(self) -> None:
        """
        Shuts down the application by stopping the background event loop and disconnecting from the broker.
        """
        # self._should_stop.set()
        if self._time_status_publisher is not None:
            self.simulator.remove_observer(self._time_status_publisher)
        self._time_status_publisher = None

        if self.connection:
            self.stop_application()
            self._consuming = False
        logger.info(f"Application {self.app_name} successfully shut down.")

    def send_message(self, app_name, app_topics, payload: str) -> None:
        """
        Sends a message to the broker. The message is sent to the exchange using the routing key. The routing key is created using the application name and topic. The message is published with an expiration of 60 seconds.

        Args:
            app_name (str): application name
            app_topics (str or list): topic name or list of topic names
            payload (str): message payload
        """
        if isinstance(app_topics, str):
            app_topics = [app_topics]

        for app_topic in app_topics:
            routing_key = self.create_routing_key(app_name=app_name, topic=app_topic)
            if not self.predefined_exchanges_queues:
                routing_key, queue_name = self.yamless_declare_bind_queue(
                    routing_key=routing_key
                )
            self.channel.basic_publish(
                exchange=self.prefix,
                routing_key=routing_key,
                body=payload,
                properties=pika.BasicProperties(
                    expiration=self.config.rc.server_configuration.servers.rabbitmq.message_expiration,
                    delivery_mode=self.config.rc.server_configuration.servers.rabbitmq.delivery_mode,
                    content_type=self.config.rc.server_configuration.servers.rabbitmq.content_type,
                    app_id=self.app_name,
                ),
            )
            logger.debug(
                f"Successfully sent message '{payload}' to topic '{routing_key}'."
            )

    def routing_key_matches_pattern(self, routing_key, pattern):
        """
        Check if a routing key matches a wildcard pattern.

        Args:
            routing_key (str): The actual routing key of the message
            pattern (str): The pattern which may contain * or # wildcards

        Returns:
            bool: True if the routing key matches the pattern
        """
        # Split both keys into segments
        route_parts = routing_key.split(".")
        pattern_parts = pattern.split(".")

        # If # isn't in pattern, both must have same number of parts
        if "#" not in pattern_parts and len(route_parts) != len(pattern_parts):
            return False

        i = 0
        while i < len(pattern_parts):
            # Handle # wildcard (matches 0 or more segments)
            if pattern_parts[i] == "#":
                return True  # # at the end matches everything remaining

            # Handle * wildcard (matches exactly one segment)
            elif pattern_parts[i] == "*":
                # Ensure there's a segment to match
                if i >= len(route_parts):
                    return False
                # * matches any single segment, continue to next segment
                i += 1
                continue

            # Handle exact match segment
            else:
                # If we've run out of route parts or segments don't match
                if i >= len(route_parts) or pattern_parts[i] != route_parts[i]:
                    return False

            i += 1

        # If we've gone through all pattern parts, make sure we've used all route parts
        return len(route_parts) <= i

    def add_message_callback(
        self, app_name: str, app_topic: str, user_callback: Callable
    ):
        """
        Add callback for a topic, supporting wildcards (* and #) in routing keys.

        * matches exactly one word
        # matches zero or more words
        """
        self.was_consuming = True
        self._consuming = True

        routing_key = self.create_routing_key(app_name=app_name, topic=app_topic)

        # Check if this is the first callback for this routing key pattern
        if routing_key not in self._callbacks_per_topic:
            self._callbacks_per_topic[routing_key] = []

            # Only set up the consumer once per topic
            if not self.predefined_exchanges_queues:
                # For wildcard subscriptions, use the app_name as queue suffix to ensure uniqueness
                queue_suffix = self.app_name

                # If using wildcards, bind to the wildcard pattern
                if "*" in routing_key or "#" in routing_key:
                    # Create a unique queue name for this wildcard subscription
                    queue_name = f"{routing_key.replace('*', 'star').replace('#', 'hash')}.{queue_suffix}"

                    # Declare a new queue
                    self.channel.queue_declare(
                        queue=queue_name, durable=False, auto_delete=True
                    )

                    # Bind queue to the exchange with the wildcard pattern
                    self.channel.queue_bind(
                        exchange=self.prefix, queue=queue_name, routing_key=routing_key
                    )

                    # Track the declared queue
                    self.declared_queues.add(queue_name)
                else:
                    # For non-wildcard keys, use the standard approach
                    routing_key, queue_name = self.yamless_declare_bind_queue(
                        routing_key=routing_key, app_specific_extender=queue_suffix
                    )

                self.channel.basic_qos(prefetch_count=1)
                self._consumer_tag = self.channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self._handle_message,
                    auto_ack=False,
                )

        # Add the callback to the list for this routing key
        self._callbacks_per_topic[routing_key].append(user_callback)

    def _handle_message(self, ch, method, properties, body):
        """
        Callback for handling messages received from RabbitMQ.
        Supports both direct routing key matches and wildcard patterns.
        """
        routing_key = method.routing_key
        logger.debug(f"Received message with routing key: {routing_key}")

        # First check for exact routing key match
        direct_callbacks = self._callbacks_per_topic.get(routing_key, [])

        # Then find any wildcard patterns that match this routing key
        wildcard_callbacks = []
        for pattern, callbacks in self._callbacks_per_topic.items():
            # Skip exact matches (already handled) and patterns that don't match
            if pattern == routing_key:
                continue

            if "*" in pattern or "#" in pattern:
                if self.routing_key_matches_pattern(routing_key, pattern):
                    wildcard_callbacks.extend(callbacks)

        # Combine all matching callbacks
        all_callbacks = direct_callbacks + wildcard_callbacks

        if all_callbacks:
            logger.debug(
                f"Found {len(all_callbacks)} callbacks for routing key: {routing_key}"
            )
        else:
            logger.debug(f"No callbacks found for routing key: {routing_key}")
            # Still acknowledge the message even if no callbacks matched
            self.acknowledge_message(method.delivery_tag)
            return

        try:
            # Execute all callbacks for this message
            for callback in all_callbacks:
                callback(ch, method, properties, body)

            # Only acknowledge after all callbacks complete successfully
            self.acknowledge_message(method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject the message if any callback fails
            if self.channel:
                self.channel.basic_reject(
                    delivery_tag=method.delivery_tag, requeue=True
                )

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        try:
            logger.debug(f"Acknowledging message {delivery_tag}")
            self.channel.basic_ack(delivery_tag, True)
        except:
            pass

    def create_routing_key(self, app_name: str, topic: str):
        """
        Creates a routing key for the application. The routing key is used to bind the queue to the exchange.

        Args:
            app_name (str): application name
            topic (str): topic name
        """
        routing_key = ".".join([self.prefix, app_name, topic])
        return routing_key

    def yamless_declare_bind_queue(
        self, routing_key: str = None, app_specific_extender: str = None
    ) -> None:
        """
        Declares and binds a queue to the exchange. The queue is bound to the exchange using the routing key. The routing key is created using the application name and topic.
        Args:
            app_name (str): application name
            topic (str): topic name
            app_specific_extender (str): application specific extender, used to create a unique queue name for the application. If the app_specific_extender is not provided, the queue name is the same as the routing key.
        """
        try:
            if app_specific_extender:
                queue_name = ".".join([routing_key, app_specific_extender])
            else:
                queue_name = routing_key
            self.channel.queue_declare(
                queue=queue_name, durable=False, auto_delete=True
            )
            self.channel.queue_bind(
                exchange=self.prefix, queue=queue_name, routing_key=routing_key
            )
            # Create list of declared queues and exchanges
            self.declared_queues.add(queue_name.strip())
            self.declared_queues.add(routing_key.strip())
            self.declared_exchanges.add(self.prefix.strip())

            logger.debug(f"Bound queue '{queue_name}' to topic '{routing_key}'.")

        except:
            routing_key = None
            queue_name = None
            pass

        return routing_key, queue_name

    def delete_queue(self, configs, app_name):
        """
        Deletes the queues from RabbitMQ.

        Args:
            configs (list): list of channel configurations
            app_name (str): application name
        """
        for config in configs:
            if config["app"] == app_name:
                logger.info(f"Deleting queue: {config['address']}")
                self.channel.queue_delete(queue=config["address"])
        logger.info("Successfully deleted queues.")

    def delete_exchange(self, unique_exchanges):
        """
        Deletes the exchanges from RabbitMQ.

        Args:
            unique_exchanges (dict): dictionary of unique exchanges
        """
        for exchange_name, exchange_config in unique_exchanges.items():
            self.channel.exchange_delete(exchange=exchange_name)
        logger.info("Successfully deleted exchanges.")

    def delete_all_queues_and_exchanges(self):
        """
        Deletes all declared queues and exchanges from RabbitMQ.
        """
        for queue_name in list(self.declared_queues):
            try:
                # self.channel.queue_purge(queue=queue_name)
                self.channel.queue_delete(queue=queue_name)
                logger.info(f"Deleted queue: {queue_name}")
            except Exception as e:
                logger.error(f"Failed to delete queue {queue_name}: {e}")

        for exchange_name in list(self.declared_exchanges):
            try:
                self.channel.exchange_delete(exchange=exchange_name)
                logger.info(f"Deleted exchange: {exchange_name}")
            except Exception as e:
                logger.error(f"Failed to delete exchange {exchange_name}: {e}")

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self.channel:
            logger.info("Sending a Basic.Cancel RPC command to RabbitMQ")
            cb = functools.partial(self.on_cancelok, userdata=self._consumer_tag)
            self.channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.
        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)
        """
        self._consuming = False
        logger.info(
            "RabbitMQ acknowledged the cancellation of the consumer: %s", userdata
        )
        self.close_channel()
        self.stop_loop()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.
        """
        logger.info("Deleting queues and exchanges.")

        if self.predefined_exchanges_queues:
            self.delete_queue(self.channel_configs, self.app_name)
            self.delete_exchange(self.unique_exchanges)
        else:
            self.delete_all_queues_and_exchanges()

        logger.info("Closing channel")
        self.channel.close()

    def stop_loop(self):
        """Stop the IO loop"""
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
        if not self._closing:
            self._closing = True
            if self._consuming:
                self.stop_consuming()
                # Signal the thread to stop
                if hasattr(self, "stop_event"):
                    self.stop_event.set()
                if hasattr(self, "_should_stop"):
                    self._should_stop.set()
                if hasattr(self, "io_thread"):
                    self._io_thread.join()
                sys.exit()
            else:
                self.connection.ioloop.stop()

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
