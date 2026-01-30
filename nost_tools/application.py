"""
Provides a base application that publishes messages from a simulator to a broker.
"""

import functools
import logging
import logging.handlers
import os
import signal
import ssl
import threading
import time
from datetime import datetime, timedelta
from typing import Callable

import ntplib
import pika
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
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

    def __init__(
        self,
        app_name: str,
        app_description: str = None,
        setup_signal_handlers: bool = True,
    ):
        """
        Initializes a new application.

        Args:
            app_name (str): application name
            app_description (str): application description (optional)
            setup_signal_handlers (bool): whether to set up signal handlers (default: True)
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
        self._reconnect_delay = None
        # Offset
        self._wallclock_refresh_thread = None
        self.wallclock_offset_refresh_interval = None
        # Set up signal handlers for graceful shutdown
        if setup_signal_handlers:
            self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """
        Sets up signal handlers for graceful shutdown on SIGINT (CTRL+C) and SIGTERM.
        """

        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            self.shut_down()

        # Register the signal handler for CTRL+C (SIGINT) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

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

    def new_access_token(self, refresh_token=None, otp=None):
        """
        Obtains a new access token and refresh token from Keycloak. If a refresh token is provided,
        the access token is refreshed using the refresh token. Otherwise, the access token is obtained
        using either:
        - User authentication: username and password (with optional OTP)
        - Service account: client credentials only

        The authentication mode is automatically detected based on whether username/password are provided.

        OTP/TOTP Handling:
        - If OTP is required but not provided, the user will be prompted to enter it interactively
        - OTP requirement is intelligently detected from Keycloak error responses
        - If credentials are incorrect, a clear error is raised without prompting for OTP

        Args:
            refresh_token (str): refresh token (optional)
            otp (str): one-time password for 2FA/MFA if required (optional)
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
                # Detect authentication mode based on presence of username/password
                has_username = self.config.rc.credentials.username is not None
                has_password = self.config.rc.credentials.password is not None

                if has_username and has_password:
                    # User authentication mode with username/password
                    logger.debug("Using user authentication (username/password)")
                    try:
                        # Try authentication with OTP if provided, otherwise without
                        token_kwargs = {
                            "grant_type": "password",
                            "username": self.config.rc.credentials.username,
                            "password": self.config.rc.credentials.password,
                        }
                        if otp:
                            token_kwargs["totp"] = otp

                        token = keycloak_openid.token(**token_kwargs)
                    except KeycloakAuthenticationError as e:
                        # Check if the error indicates OTP is required
                        error_msg = str(e).lower()
                        error_body = ""
                        if hasattr(e, 'response_body') and e.response_body:
                            try:
                                error_body = e.response_body.decode('utf-8').lower()
                            except:
                                pass

                        # Look for OTP/TOTP requirement indicators in error message or response body
                        otp_indicators = ['otp', 'totp', 'one-time', 'two-factor', '2fa', 'mfa']
                        is_otp_required = any(indicator in error_msg or indicator in error_body
                                             for indicator in otp_indicators)

                        if is_otp_required:
                            # OTP is required but wasn't provided or was incorrect
                            if otp:
                                # OTP was provided but is incorrect
                                logger.error(f"Authentication failed with provided OTP: {e}")
                                raise Exception(
                                    f"Authentication failed. The provided OTP may be incorrect or expired. "
                                    f"Error: {e}"
                                )
                            else:
                                # OTP wasn't provided, prompt for it
                                logger.info("OTP/TOTP is required for this account")
                                otp_input = input("Enter OTP: ")
                                try:
                                    token = keycloak_openid.token(
                                        grant_type="password",
                                        username=self.config.rc.credentials.username,
                                        password=self.config.rc.credentials.password,
                                        totp=otp_input,
                                    )
                                except KeycloakAuthenticationError as otp_error:
                                    logger.error(f"Authentication failed with OTP: {otp_error}")
                                    raise Exception(
                                        f"Authentication failed. Please check your credentials and OTP. "
                                        f"Error: {otp_error}"
                                    )
                        else:
                            # Credentials are likely incorrect
                            logger.error(f"Authentication failed: {e}")
                            raise Exception(
                                f"Authentication failed. Please check your username and password. "
                                f"Error: {e}"
                            )
                else:
                    # Service account authentication mode with client credentials
                    logger.debug("Using service account authentication (client credentials)")
                    token = keycloak_openid.token(grant_type=["client_credentials"])

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
        """
        logger.debug("Starting refresh token thread.")

        def refresh_token_periodically():
            while not self._should_stop.wait(timeout=self.token_refresh_interval):
                logger.debug("Token refresh thread is running.")
                try:
                    access_token, refresh_token = self.new_access_token(
                        self.refresh_token
                    )
                    self.refresh_token = refresh_token
                    self.update_connection_credentials(access_token)
                except Exception as e:
                    logger.debug(f"Failed to refresh access token: {e}")

        self._token_refresh_thread = threading.Thread(target=refresh_token_periodically)
        self._token_refresh_thread.start()
        logger.debug("Starting refresh token thread successfully completed.")

    def start_wallclock_refresh_thread(self):  # , interval=30, host="pool.ntp.org"):
        """
        Starts a background thread to refresh the wallclock offset periodically.

        Args:
            interval (int): Seconds between wallclock offset refreshes (default: 3600 seconds/1 hour)
            host (str): NTP host to query (default: 'pool.ntp.org')
        """
        logger.debug("Starting wallclock offset refresh thread.")

        def refresh_wallclock_periodically():
            while not self._should_stop.wait(
                timeout=self.config.rc.simulation_configuration.execution_parameters.general.wallclock_offset_refresh_interval
            ):
                logger.debug("Wallclock refresh thread is running.")
                try:
                    logger.debug(
                        f"Contacting {self.config.rc.simulation_configuration.execution_parameters.general.ntp_host} to retrieve wallclock offset."
                    )
                    response = ntplib.NTPClient().request(
                        self.config.rc.simulation_configuration.execution_parameters.general.ntp_host,
                        version=3,
                        timeout=2,
                    )
                    offset = timedelta(seconds=response.offset)
                    self.simulator.set_wallclock_offset(offset)
                    logger.debug(f"Wallclock offset updated to {offset}.")
                except Exception as e:
                    logger.debug(f"Failed to refresh wallclock offset: {e}")

        self._wallclock_refresh_thread = threading.Thread(
            target=refresh_wallclock_periodically
        )
        self._wallclock_refresh_thread.start()
        logger.debug("Starting wallclock offset refresh thread successfully completed.")

    def update_connection_credentials(self, access_token):
        """
        Updates the connection credentials with the new access token.

        Args:
            access_token (str): new access token
        """
        self.connection.update_secret(access_token, "secret")

    def _get_parameters_from_config(self):
        """
        Gets application parameters from configuration or returns None if not available.
        This method can be overridden by subclasses to customize parameter retrieval.

        Returns:
            object: Configuration parameters object or None
        """
        if self.config and self.config.rc.yaml_file:
            try:
                applications_dict = getattr(
                    self.config.rc.simulation_configuration.execution_parameters,
                    "applications",
                    None,
                )
                if applications_dict and self.app_name in applications_dict:
                    return applications_dict[self.app_name]
                return None
            except (AttributeError, KeyError):
                return None
        return None

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
        self.config = config

        if self.config.rc.yaml_file:
            logger.info(
                f"Collecting start up parameters from YAML configuration file: {self.config.rc.yaml_file}"
            )
            parameters = self._get_parameters_from_config()
            if parameters:
                self.set_offset = getattr(parameters, "set_offset", set_offset)
                self.time_status_step = getattr(
                    parameters, "time_status_step", time_status_step
                )
                self.time_status_init = getattr(
                    parameters, "time_status_init", time_status_init
                )
                self.shut_down_when_terminated = getattr(
                    parameters, "shut_down_when_terminated", shut_down_when_terminated
                )

                # Configure file logging if requested
                if getattr(parameters, "enable_file_logging", False):
                    self.configure_file_logging(
                        log_dir=getattr(parameters, "log_dir", None),
                        log_filename=getattr(parameters, "log_filename", None),
                        log_level=getattr(parameters, "log_level", None),
                        max_bytes=getattr(parameters, "max_bytes", None),
                        backup_count=getattr(parameters, "backup_count", None),
                        log_format=getattr(parameters, "log_format", None),
                    )
            else:
                logger.warning("No parameters found in configuration, using defaults")
                self.set_offset = set_offset
                self.time_status_step = time_status_step
                self.time_status_init = time_status_init
                self.shut_down_when_terminated = shut_down_when_terminated
        else:
            logger.info(
                f"Collecting start up parameters from user input or default values."
            )
            self.set_offset = set_offset
            self.time_status_step = time_status_step
            self.time_status_init = time_status_init
            self.shut_down_when_terminated = shut_down_when_terminated

        if self.set_offset:
            # Start periodic wallclock offset updates instead of one-time call
            logger.info(
                f"Wallclock offset will be set every {self.config.rc.simulation_configuration.execution_parameters.general.wallclock_offset_refresh_interval} seconds using {self.config.rc.simulation_configuration.execution_parameters.general.ntp_host}."
            )
            self.start_wallclock_refresh_thread()

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
            port=self.config.rc.server_configuration.servers.rabbitmq.port,
            virtual_host=self.config.rc.server_configuration.servers.rabbitmq.virtual_host,
            credentials=credentials,
            channel_max=config.rc.server_configuration.servers.rabbitmq.channel_max,
            frame_max=config.rc.server_configuration.servers.rabbitmq.frame_max,
            heartbeat=config.rc.server_configuration.servers.rabbitmq.heartbeat,
            connection_attempts=config.rc.server_configuration.servers.rabbitmq.connection_attempts,
            retry_delay=config.rc.server_configuration.servers.rabbitmq.retry_delay,
            socket_timeout=config.rc.server_configuration.servers.rabbitmq.socket_timeout,
            stack_timeout=config.rc.server_configuration.servers.rabbitmq.stack_timeout,
            locale=config.rc.server_configuration.servers.rabbitmq.locale,
            blocked_connection_timeout=config.rc.server_configuration.servers.rabbitmq.blocked_connection_timeout,
        )

        # Configure transport layer security (TLS) if needed
        if self.config.rc.server_configuration.servers.rabbitmq.tls:
            logger.info("Using TLS/SSL.")
            # SSL Context for TLS configuration of Amazon MQ for RabbitMQ
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.set_ciphers("ECDHE+AESGCM:!ECDSA")
            parameters.ssl_options = pika.SSLOptions(context=ssl_context)

        # Save connection parameters for reconnection
        self._connection_parameters = parameters
        self._reconnect_delay = (
            self.config.rc.server_configuration.servers.rabbitmq.reconnect_delay
        )
        self._queue_max_size = (
            self.config.rc.server_configuration.servers.rabbitmq.queue_max_size
        )

        # Establish non-blocking connection to RabbitMQ
        self.connection = pika.SelectConnection(
            parameters=parameters,
            on_open_callback=self.on_connection_open,
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
        Starts the I/O loop in a separate thread. This allows the application to
        run in the background while still being able to process messages from RabbitMQ.
        """
        self.stop_event = threading.Event()
        while not self.stop_event.is_set():
            try:
                self.connection.ioloop.start()
            except Exception as e:
                logger.error(f"I/O loop error: {e}")
                break

    def on_channel_open(self, channel):
        """
        Callback function for when the channel is opened.

        Args:
            channel (:obj:`pika.channel.Channel`): channel object
        """
        self.channel = channel
        self.add_on_channel_close_callback()

        # Establish the exchange for this application
        if self.prefix:
            self.establish_exchange()

        # Signal that connection is established
        self._is_connected.set()

        # Re-establish callbacks if this is a reconnection
        if hasattr(self, "_saved_callbacks") and self._saved_callbacks:
            logger.info(f"Restoring {len(self._saved_callbacks)} message callbacks")
            for app_name, app_topic, user_callback in self._saved_callbacks:
                # Pass through existing add_message_callback to handle all logic consistently
                self.add_message_callback(app_name, app_topic, user_callback)

        # Process any queued messages now that we're connected
        if hasattr(self, "_message_queue") and self._message_queue:
            # Schedule message processing to happen after all initialization
            self.connection.ioloop.call_later(0.1, self._process_message_queue)

    def establish_exchange(self):
        """
        Establishes the exchange for the application.
        """
        logger.debug(f"Declaring exchange: {self.prefix}")
        self.channel.exchange_declare(
            exchange=self.prefix,
            exchange_type="topic",
            durable=True,
            auto_delete=True,
        )

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.
        """
        logger.debug("Adding channel close callback")
        self.channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """
        Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Determines whether to close the connection or just prepare for reconnection.

        Args:
            channel (:obj:`pika.channel.Channel`): channel object
            reason (Exception): exception representing reason for channel closure
        """
        reply_code = 0
        if hasattr(reason, "reply_code"):
            reply_code = reason.reply_code

        logger.debug(f"Channel was closed: {reason} (code: {reply_code})")

        # Clear channel reference
        self.channel = None

        # # Clear consumer tag reference
        # if hasattr(self, "_consumer_tag"):
        #     self._consumer_tag = None

        # Check if this is part of an intentional shutdown
        if self._closing:
            logger.info(
                "Connection closed intentionally. Proceeding with connection closure."
            )
            # During intentional shutdown, proceed with connection closure
            self.close_connection()
            return

        # If unexpected closure, wait for reconnection
        logger.info(
            f"Connection closed unexpectedly. Reconnecting in {self._reconnect_delay} seconds."
        )

    def close_connection(self):
        """
        This method is invoked by pika when the connection to RabbitMQ is
        closed. This method is called when the application is shutting down
        or when the connection is closed unexpectedly.
        """
        self._consuming = False
        if self.connection.is_closing or self.connection.is_closed:
            logger.info("Connection is closing or already closed")
        else:
            logger.info("Closing connection")
            self.connection.close()

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
        Invoked by pika when RabbitMQ unexpectedly closes the connection.
        Determines whether to close the connection or just prepare for reconnection.

        Args:
            connection (:obj:`pika.connection.Connection`): connection object
            reason (Exception): exception representing reason for loss of connection
        """
        # First clear the channel reference regardless of reason
        self.channel = None

        # Check if this is an intentional closure (self._closing is True)
        if self._closing:
            # Resources already cleaned up in stop_application()
            logger.debug(
                "Connection closed after intentional stop, cleanup already performed."
            )
            self.connection.ioloop.stop()
        else:
            # This is an unexpected connection drop - don't delete queues or exchanges
            logger.debug(
                f"Connection closed unexpectedly, reconnecting in {self._reconnect_delay} seconds: {reason}."
            )
            # Schedule reconnection
            self.connection.ioloop.call_later(self._reconnect_delay, self.reconnect)

    def on_connection_open(self, connection):
        """
        This method is invoked by pika when the connection to RabbitMQ has
        been established. At this point we can create a channel and start
        consuming messages.

        Args:
            connection (:obj:`pika.connection.Connection`): connection object
        """
        self.connection = connection
        self.connection.channel(on_open_callback=self.on_channel_open)
        # logger.info("Connection established successfully.")

    def reconnect(self):
        """
        Reconnect to RabbitMQ by reinitializing the connection with refreshed credentials.
        """
        if not self._closing:
            try:
                logger.info("Attempting to reconnect to RabbitMQ.")

                # Reset callback tracking dictionary but keep saved callbacks
                self._callbacks_per_topic = {}

                # Refresh the token if Keycloak authentication is enabled
                if (
                    self.config.rc.server_configuration.servers.rabbitmq.keycloak_authentication
                ):
                    try:
                        logger.debug("Refreshing access token before reconnection...")
                        access_token, refresh_token = self.new_access_token(
                            self.refresh_token
                        )
                        self.refresh_token = refresh_token

                        # Update connection parameters with new credentials
                        self._connection_parameters.credentials = pika.PlainCredentials(
                            "", access_token
                        )
                        logger.debug(
                            "Access token refreshed successfully for reconnection"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to refresh token during reconnection: {e}"
                        )
                        # Continue with existing token, it might still work

                # Save reference to old connection's ioloop before creating new one
                old_ioloop = self.connection.ioloop if self.connection else None

                self.connection = pika.SelectConnection(
                    parameters=self._connection_parameters,
                    on_open_callback=self.on_connection_open,
                    on_open_error_callback=self.on_connection_error,
                    on_close_callback=self.on_connection_closed,
                )

                # Stop the old ioloop so _start_io_loop's while loop can continue
                # with the new connection. Don't start a new thread.
                if old_ioloop:
                    old_ioloop.stop()
                logger.info(
                    "Reconnection initiated, new connection will be processed by existing IO thread."
                )

            except Exception as e:
                logger.error(f"Reconnection attempt failed: {e}")
                # Use Timer instead of call_later since ioloop may be stopped/inconsistent
                timer = threading.Timer(self._reconnect_delay, self.reconnect)
                timer.daemon = True
                timer.start()

    def shut_down(self) -> None:
        """
        Shuts down the application by stopping the background event loop and disconnecting from the broker.
        """
        logger.info(f"Initiating shutdown of {self.app_name}")

        # Clean up simulator-related resources
        if self._time_status_publisher is not None:
            self.simulator.remove_observer(self._time_status_publisher)
        self._time_status_publisher = None

        # Clean up connection-related resources
        if self.connection and not self._closing:
            logger.info(f"Shutting down {self.app_name} connection.")
            self.stop_application()
            self._consuming = False

        # Signal all threads to stop
        if hasattr(self, "stop_event"):
            self.stop_event.set()
        if hasattr(self, "_should_stop"):
            self._should_stop.set()

        # Comprehensive resource cleanup
        self._cleanup_resources()

        logger.info(f"Shutdown of {self.app_name} completed successfully.")

        # Exit the process
        os._exit(0)

    def _cleanup_resources(self):
        """
        Comprehensive cleanup of both multiprocessing resource tracker and joblib resources.
        Handles cleanup in the correct order to prevent resource leaks and warnings.
        """
        try:
            import gc
            import sys
            import warnings

            # Suppress resource tracker warnings
            warnings.filterwarnings("ignore", category=UserWarning, module="joblib")
            warnings.filterwarnings(
                "ignore",
                category=UserWarning,
                message="resource_tracker: There appear to be.*leaked.*objects",
            )

            # 1. First cleanup joblib resources (if joblib is used)
            joblib_used = "joblib" in sys.modules
            if joblib_used:
                logger.debug("Cleaning up joblib resources")
                try:
                    import joblib
                    from joblib.externals.loky import process_executor

                    # Force garbage collection to help break reference cycles
                    gc.collect()

                    # Clear any joblib Memory caches
                    memory_locations = []
                    for obj in gc.get_objects():
                        if isinstance(obj, joblib.Memory):
                            memory_locations.append(obj.location)
                            obj.clear()

                    if memory_locations:
                        logger.debug(
                            f"Cleared {len(memory_locations)} joblib memory caches"
                        )

                    # Find and terminate any active Parallel instances
                    terminated_count = 0
                    for obj in gc.get_objects():
                        try:
                            if (
                                hasattr(obj, "_backend")
                                and hasattr(obj, "n_jobs")
                                and hasattr(obj, "_terminate")
                            ):
                                obj._terminate()
                                terminated_count += 1
                        except Exception:
                            pass

                    if terminated_count:
                        logger.debug(
                            f"Terminated {terminated_count} joblib Parallel instances"
                        )

                    # Reset the process executor state
                    process_executor._CURRENT_DEPTH = 0
                    if hasattr(process_executor, "_INITIALIZER"):
                        process_executor._INITIALIZER = None
                    if hasattr(process_executor, "_INITARGS"):
                        process_executor._INITARGS = ()

                except Exception as e:
                    logger.debug(f"Error during joblib cleanup: {e}")

            # 2. Then clean up multiprocessing resource tracker
            try:
                import multiprocessing.resource_tracker as resource_tracker

                # Force resource tracker to clean up resources
                if (
                    hasattr(resource_tracker, "_resource_tracker")
                    and resource_tracker._resource_tracker is not None
                ):

                    logger.debug("Cleaning up resource tracker")
                    tracker = resource_tracker._resource_tracker

                    if hasattr(tracker, "_resources"):
                        for resource_type in list(tracker._resources.keys()):
                            resources = tracker._resources.get(resource_type, set())
                            if resources:
                                logger.debug(
                                    f"Cleaning up {len(resources)} {resource_type} resources"
                                )
                                resources_copy = resources.copy()
                                for resource in resources_copy:
                                    try:
                                        resources.discard(resource)
                                    except Exception as e:
                                        logger.debug(
                                            f"Error discarding {resource_type} resource: {e}"
                                        )

                        # Final safety check - clear all remaining resources
                        tracker._resources.clear()

                # Force garbage collection after cleanup
                gc.collect()

            except (ImportError, AttributeError, Exception) as e:
                logger.debug(f"Error during resource tracker cleanup: {e}")

        except Exception as e:
            logger.warning(f"Error during resource cleanup: {e}")

    def _build_basic_properties(self) -> pika.BasicProperties:
        """
        Build BasicProperties for message publishing, only including non-None values.
        This prevents protocol errors when None values are passed to RabbitMQ.

        Returns:
            pika.BasicProperties: Properties object with only non-None values
        """
        properties_dict = {}
        rabbitmq_config = self.config.rc.server_configuration.servers.rabbitmq

        if rabbitmq_config.content_type is not None:
            properties_dict['content_type'] = rabbitmq_config.content_type
        if rabbitmq_config.content_encoding is not None:
            properties_dict['content_encoding'] = rabbitmq_config.content_encoding
        if rabbitmq_config.headers is not None:
            properties_dict['headers'] = rabbitmq_config.headers
        if rabbitmq_config.delivery_mode is not None:
            properties_dict['delivery_mode'] = rabbitmq_config.delivery_mode
        if rabbitmq_config.priority is not None:
            properties_dict['priority'] = rabbitmq_config.priority
        if rabbitmq_config.correlation_id is not None:
            properties_dict['correlation_id'] = rabbitmq_config.correlation_id
        if rabbitmq_config.reply_to is not None:
            properties_dict['reply_to'] = rabbitmq_config.reply_to
        if rabbitmq_config.message_expiration is not None:
            properties_dict['expiration'] = rabbitmq_config.message_expiration
        if rabbitmq_config.message_id is not None:
            properties_dict['message_id'] = rabbitmq_config.message_id
        if rabbitmq_config.timestamp is not None:
            properties_dict['timestamp'] = rabbitmq_config.timestamp
        if rabbitmq_config.type is not None:
            properties_dict['type'] = rabbitmq_config.type
        if rabbitmq_config.user_id is not None:
            properties_dict['user_id'] = rabbitmq_config.user_id
        if rabbitmq_config.app_id is not None:
            properties_dict['app_id'] = rabbitmq_config.app_id
        if rabbitmq_config.cluster_id is not None:
            properties_dict['cluster_id'] = rabbitmq_config.cluster_id

        return pika.BasicProperties(**properties_dict)

    def send_message(self, app_name, app_topics, payload: str) -> None:
        """
        Sends a message to the broker. If the connection is down, the message is queued
        for later delivery when the connection is restored.

        Args:
            app_name (str): application name
            app_topics (str or list): topic name or list of topic names
            payload (str): message payload
        """
        # Initialize message queue if it doesn't exist
        if not hasattr(self, "_message_queue"):
            self._message_queue = []
            # self._queue_max_size = 1000  # Limit queue size to prevent memory issues

        if isinstance(app_topics, str):
            app_topics = [app_topics]

        # Check if channel is available
        if self.channel is None or not self._is_connected.is_set():
            logger.warning(f"Connection down, queueing message for later delivery")

            # Queue the message if there's space available
            if len(self._message_queue) < self._queue_max_size:
                # Add timestamp to each message for FIFO ordering
                timestamp = time.time()
                for app_topic in app_topics:
                    self._message_queue.append(
                        (timestamp, app_name, app_topic, payload)
                    )
                    logger.info(
                        f"Queued message for topic {app_topic} (queue size: {len(self._message_queue)})"
                    )
            else:
                logger.error(f"Message queue full, dropping message for {app_topics}")
            return

        # Try to send any queued messages first
        self._process_message_queue()

        # Now send the current message
        for app_topic in app_topics:
            routing_key = self.create_routing_key(app_name=app_name, topic=app_topic)
            try:
                self.channel.basic_publish(
                    exchange=self.prefix,
                    routing_key=routing_key,
                    body=payload,
                    properties=self._build_basic_properties(),
                )
                logger.debug(
                    f"Successfully sent message '{payload}' to topic '{routing_key}'."
                )
            except Exception as e:
                logger.warning(f"Failed to publish message to {routing_key}: {e}")
                # Queue the failed message if there's space available
                if len(self._message_queue) < self._queue_max_size:
                    timestamp = time.time()
                    self._message_queue.append(
                        (timestamp, app_name, app_topic, payload)
                    )
                    logger.info(
                        f"Queued failed message for retry (queue size: {len(self._message_queue)})"
                    )

    def _process_message_queue(self):
        """
        Process queued messages when connection is available.
        Attempts to send all queued messages in order of oldest first.
        """
        if not hasattr(self, "_message_queue") or not self._message_queue:
            return  # No messages to process

        if self.channel is None or not self._is_connected.is_set():
            return  # Still no connection

        # Process the queue in timestamp order (oldest first)
        logger.info(f"Processing message queue ({len(self._message_queue)} messages)")

        # Sort messages by timestamp (oldest first)
        sorted_messages = sorted(self._message_queue, key=lambda x: x[0])
        self._message_queue.clear()

        success_count = 0
        for timestamp, app_name, app_topic, payload in sorted_messages:
            routing_key = self.create_routing_key(app_name=app_name, topic=app_topic)
            try:
                self.channel.basic_publish(
                    exchange=self.prefix,
                    routing_key=routing_key,
                    body=payload,
                    properties=self._build_basic_properties(),
                )
                success_count += 1
            except Exception as e:
                # If sending still fails, put it back in the queue with original timestamp
                # to preserve ordering
                logger.warning(f"Failed to resend queued message to {routing_key}: {e}")
                self._message_queue.append((timestamp, app_name, app_topic, payload))

        if success_count > 0:
            logger.info(f"Successfully sent {success_count} queued messages")

        if self._message_queue:
            logger.info(
                f"{len(self._message_queue)} messages remain queued for later delivery"
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
        (* matches exactly one word, # matches zero or more words)

        Args:
            app_name (str): application name
            app_topic (str): topic name
            user_callback (Callable): callback function to be called when a message is received
        """
        self.was_consuming = True
        self._consuming = True

        # Store callback for reconnection
        if not hasattr(self, "_saved_callbacks"):
            self._saved_callbacks = []

        # Don't duplicate callbacks in saved list
        callback_info = (app_name, app_topic, user_callback)
        if callback_info not in self._saved_callbacks:
            self._saved_callbacks.append(callback_info)

        routing_key = self.create_routing_key(app_name=app_name, topic=app_topic)

        # Check if this is the first callback for this routing key pattern
        if routing_key not in self._callbacks_per_topic:
            self._callbacks_per_topic[routing_key] = []

            # Only set up the consumer once per topic
            if not self.predefined_exchanges_queues:
                # For wildcard subscriptions, use the app_name as queue suffix to ensure uniqueness
                queue_suffix = self.app_name
                queue_name = None

                # If using wildcards, bind to the wildcard pattern
                if "*" in routing_key or "#" in routing_key:
                    # Create a unique queue name for this wildcard subscription
                    queue_name = f"{routing_key.replace('*', 'star').replace('#', 'hash')}.{queue_suffix}"

                    # Declare a new queue
                    self.channel.queue_declare(
                        queue=queue_name, durable=True, auto_delete=False
                    )

                    # Bind queue to the exchange with the wildcard pattern
                    self.channel.queue_bind(
                        exchange=self.prefix, queue=queue_name, routing_key=routing_key
                    )

                    # Track the declared queue and exchange
                    self.declared_queues.add(queue_name)
                    self.declared_exchanges.add(self.prefix.strip())

                    # # Also track the routing key if it's used for binding
                    # if routing_key != queue_name:
                    #     self.declared_queues.add(routing_key.strip())
                else:
                    # For non-wildcard keys, use the standard approach
                    routing_key, queue_name = self.yamless_declare_bind_queue(
                        routing_key=routing_key, app_specific_extender=queue_suffix
                    )

                if queue_name:
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

        Args:
            ch (:obj:`pika.channel.Channel`): channel object
            method (:obj:`pika.spec.Basic.Deliver`): method frame
            properties (:obj:`pika.spec.BasicProperties`): properties frame
            body (str): message body
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

        Args:
            delivery_tag (str): The delivery tag of the message to acknowledge
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
            routing_key (str): routing key
            app_specific_extender (str): application-specific extender for the queue name
        """
        try:
            if app_specific_extender:
                queue_name = ".".join([routing_key, app_specific_extender])
            else:
                queue_name = routing_key
            self.channel.queue_declare(
                queue=queue_name, durable=True, auto_delete=False
            )
            self.channel.queue_bind(
                exchange=self.prefix, queue=queue_name, routing_key=routing_key
            )
            # Create list of declared queues and exchanges
            self.declared_queues.add(queue_name.strip())
            # self.declared_queues.add(routing_key.strip())
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
                logger.debug(f"Deleting queue: {config['address']}")
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

    def _delete_queues_with_callback(self, completion_event):
        """
        Deletes all declared queues from RabbitMQ with proper callbacks,
        and signals the completion_event when done.
        Does NOT delete exchanges - those are managed exclusively by the Manager class.

        Args:
            completion_event (threading.Event): Event to signal when deletion is complete
        """
        if not self.channel or self.channel.is_closed:
            logger.warning("Cannot delete queues: channel is closed")
            completion_event.set()  # Signal completion since we can't proceed
            return

        # Create copies to avoid modification during iteration
        queues_to_delete = list(self.declared_queues)

        # If nothing to delete, signal completion immediately
        if not queues_to_delete:
            logger.info("No queues to delete")
            completion_event.set()
            return

        # Track how many queues are still pending deletion
        pending_deletions = len(queues_to_delete)

        # Callback functions
        def on_queue_purged(method_frame, queue_name):
            """Callback for queue purge"""
            logger.debug(f"Successfully purged queue: {queue_name}")
            # After purging, unbind the queue
            unbind_queue_from_exchanges(queue_name)

        def on_queue_unbind_ok(
            method_frame, queue_name, current_exchange, remaining_exchanges
        ):
            """Callback for queue unbind"""
            logger.debug(
                f"Successfully unbound queue {queue_name} from exchange {current_exchange}"
            )
            if remaining_exchanges:
                # Continue unbinding from next exchange
                next_exchange = remaining_exchanges[0]
                try:
                    self.channel.queue_unbind(
                        queue=queue_name,
                        exchange=next_exchange,
                        routing_key=queue_name,
                        callback=lambda method_frame: on_queue_unbind_ok(
                            method_frame,
                            queue_name,
                            next_exchange,
                            remaining_exchanges[1:],
                        ),
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to unbind queue {queue_name} from exchange {next_exchange}: {e}"
                    )
                    # Continue with queue deletion even if unbinding fails
                    delete_queue(queue_name)
            else:
                # All unbinds complete, delete queue
                delete_queue(queue_name)

        def on_queue_deleted(method_frame, queue_name):
            """Callback for queue delete"""
            nonlocal pending_deletions
            logger.debug(f"Successfully deleted queue: {queue_name}")
            self.declared_queues.discard(queue_name)

            # Decrement pending deletions counter
            pending_deletions -= 1

            # When all queues are deleted, signal completion
            if pending_deletions == 0:
                logger.debug("All queues have been deleted.")
                completion_event.set()

        def unbind_queue_from_exchanges(queue_name):
            """Unbind queue from each exchange"""
            exchanges_to_unbind_from = list(self.declared_exchanges)
            if exchanges_to_unbind_from:
                first_exchange = exchanges_to_unbind_from[0]
                try:
                    if first_exchange and first_exchange != "":
                        logger.debug(
                            f"Unbinding queue {queue_name} from exchange {first_exchange}"
                        )
                        self.channel.queue_unbind(
                            queue=queue_name,
                            exchange=first_exchange,
                            routing_key=queue_name,
                            callback=lambda method_frame: on_queue_unbind_ok(
                                method_frame,
                                queue_name,
                                first_exchange,
                                exchanges_to_unbind_from[1:],
                            ),
                        )
                    else:
                        # Skip empty exchange, move to next
                        on_queue_unbind_ok(
                            None,
                            queue_name,
                            first_exchange,
                            exchanges_to_unbind_from[1:],
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to unbind queue {queue_name} from exchange {first_exchange}: {e}"
                    )
                    # Continue with queue deletion even if unbinding fails
                    delete_queue(queue_name)
            else:
                # No exchanges to unbind from, proceed with delete
                delete_queue(queue_name)

        def delete_queue(queue_name):
            """Delete a queue with callback"""
            try:
                logger.debug(f"Deleting queue: {queue_name}")
                self.channel.queue_delete(
                    queue=queue_name,
                    if_unused=False,
                    if_empty=False,
                    callback=lambda method_frame: on_queue_deleted(
                        method_frame, queue_name
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to delete queue {queue_name}: {e}")
                # Remove from tracking even if deletion fails and update counter
                self.declared_queues.discard(queue_name)
                nonlocal pending_deletions
                pending_deletions -= 1

                # Check if this was the last queue
                if pending_deletions == 0:
                    # All queues processed (or failed), signal completion
                    completion_event.set()

        # Start the deletion process for each queue
        for queue_name in queues_to_delete:
            try:
                logger.debug(f"Attempting to purge queue: {queue_name}")
                self.channel.queue_purge(
                    queue=queue_name,
                    callback=lambda method_frame, q=queue_name: on_queue_purged(
                        method_frame, q
                    ),
                )
            except Exception as e:
                logger.debug(f"Failed to purge queue {queue_name}: {e}")
                # Continue with unbinding even if purge fails
                unbind_queue_from_exchanges(queue_name)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self.channel:
            logger.debug("Sending a Basic.Cancel RPC command to RabbitMQ")
            cb = functools.partial(self.on_cancelok, userdata=self._consumer_tag)
            self.channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        Args:
            _unused_frame (:obj:`pika.frame.Method`): The Basic.CancelOk frame
            userdata (str|unicode): Extra user data (consumer tag)
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
        logger.info("Closing channel")
        self.channel.close()

    def stop_loop(self):
        """Stop the IO loop"""
        self.connection.ioloop.stop()

    def stop_application(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ, cleaning up resources, and stopping all background threads.
        """
        if not self._closing:
            self._closing = True
            logger.debug("Initiating application shutdown sequence")

            # Create a threading Event to signal when cleanup is complete
            cleanup_complete_event = threading.Event()

            # First clean up RabbitMQ resources if channel is available
            if (
                self.channel
                and not self.channel.is_closing
                and not self.channel.is_closed
            ):
                try:
                    # Clean up resources before stopping the loop
                    if self.predefined_exchanges_queues:
                        self.delete_queue(self.channel_configs, self.app_name)
                        self.delete_exchange(self.unique_exchanges)
                        # Signal completion immediately for simple delete operations
                        cleanup_complete_event.set()
                    else:
                        # Delete all queues and exchanges with a callback for completion
                        self._delete_queues_with_callback(cleanup_complete_event)
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")
                    # Set the event even if there's an error
                    cleanup_complete_event.set()
            else:
                # No channel available, so cleanup is "complete"
                cleanup_complete_event.set()

            # Wait for cleanup to complete with a reasonable timeout (10 seconds)
            logger.info("Cleaning up queues.")
            cleanup_result = cleanup_complete_event.wait(timeout=10)
            if cleanup_result:
                logger.info("Cleaning up queues completed successfully.")
            else:
                logger.warning("Cleaning up queues timed out after 10 seconds.")

            # Also stop token refresh thread if it exists
            if hasattr(self, "_should_stop"):
                self._should_stop.set()
            if (
                hasattr(self, "_token_refresh_thread")
                and self._token_refresh_thread
                and self._token_refresh_thread.is_alive()
            ):
                logger.info("Closing token refresh thread.")
                # Set a timeout to avoid hanging indefinitely
                self._token_refresh_thread.join(timeout=60.0)
                # Check if it's still alive after timeout
                if self._token_refresh_thread.is_alive():
                    logger.warning(
                        "Closing token refresh thread timed out after 60 seconds. "
                    )
                else:
                    logger.info("Closing token refresh thread completed successfully")
            # Also stop wallclock refresh thread if it exists
            if (
                hasattr(self, "_wallclock_refresh_thread")
                and self._wallclock_refresh_thread
                and self._wallclock_refresh_thread.is_alive()
            ):
                logger.info("Closing wallclock refresh thread.")
                # Set a timeout to avoid hanging indefinitely
                self._wallclock_refresh_thread.join(timeout=60.0)
                # Check if it's still alive after timeout
                if self._wallclock_refresh_thread.is_alive():
                    logger.warning(
                        "Closing wallclock refresh thread timed out after 60 seconds. "
                    )
                else:
                    logger.info(
                        "Closing wallclock refresh thread completed successfully"
                    )
            logger.debug("Stop_application completed successfully.")

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
        Creates a shut down observer to close the application when the simulator is terminated.
        """
        if self._shut_down_observer is not None:
            self.simulator.remove_observer(self._shut_down_observer)
        self._shut_down_observer = ShutDownObserver(self)
        self.simulator.add_observer(self._shut_down_observer)

    def configure_file_logging(
        self,
        log_dir: str = None,
        log_filename: str = None,
        log_level: str = None,
        max_bytes: int = None,
        backup_count: int = None,
        log_format: str = None,
    ):
        """
        Configures file logging for the application.

        Args:
            log_dir (str): Directory where log files will be stored
            log_filename (str): Name of the log file. If None, a timestamped filename will be used
            log_level (str): Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            max_bytes (int): Maximum file size in bytes before rotating
            backup_count (int): Number of backup files to keep
            log_format (str): Log message format
        """
        try:
            if log_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = os.path.join(log_dir, f"{self.app_name}_{timestamp}.log")
            else:
                log_filename = os.path.join(log_dir, log_filename)

            # Create log directory if it doesn't exist
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                logger.info(f"Log directory {log_dir} successfully created.")

            # Configure rotating file handler
            handler = logging.handlers.RotatingFileHandler(
                log_filename, maxBytes=max_bytes, backupCount=backup_count
            )

            # Set log level
            level = getattr(logging, log_level.upper(), logging.INFO)
            handler.setLevel(level)

            # Set log format
            if log_format is not None:
                formatter = logging.Formatter(log_format)
                handler.setFormatter(formatter)
            else:
                # Default format
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                handler.setFormatter(formatter)

            # Add the handler to the root logger
            logging.getLogger().addHandler(handler)
            logger.info(f"File logging configured: {log_filename} (level: {log_level})")
        except Exception as e:
            logger.error(f"Error configuring file logging: {e}")

    def request_resume(
        self, sim_resume_time: datetime = None, tolerance: timedelta = None
    ) -> None:
        """
        Request a resume from the manager with optional scenario time and tolerance.

        Args:
            sim_resume_time (:obj:`datetime`, optional): Scenario time at which to resume.
                If None, resume immediately.
            tolerance (:obj:`timedelta`, optional): Time tolerance for resume. If not provided,
                uses default from configuration_parameters['resume_tolerance'] if available.
                If tolerance is None (not provided and not in config), resume immediately.
        """
        from .schemas import ResumeRequest

        # If tolerance not provided, get default from general config (defaults to 12 hours)
        if tolerance is None and self.config and self.config.rc.yaml_file:
            try:
                general_config = self.config.rc.simulation_configuration.execution_parameters.general
                if general_config and general_config.resume_tolerance:
                    tolerance = general_config.resume_tolerance
            except (AttributeError, KeyError):
                # If not in config, will remain None and resume immediately
                pass

        # Build request parameters
        request_params = {"requestingApp": self.app_name}
        if sim_resume_time is not None:
            request_params["simResumeTime"] = sim_resume_time
        if tolerance is not None:
            request_params["tolerance"] = tolerance

        # Create the resume request
        request = ResumeRequest.model_validate({"taskingParameters": request_params})

        logger.info(f"Requesting resume: {request.model_dump_json(by_alias=True)}")

        # Send the request to the manager
        self.send_message(
            app_name=self.app_name,
            app_topics="request.resume",
            payload=request.model_dump_json(by_alias=True),
        )
