"""
Provides a base logger application that subscribes and writes all messages to file.
"""

import logging
import os
from datetime import datetime, timedelta

from .application import Application
from .configuration import ConnectionConfig

logger = logging.getLogger(__name__)


class LoggerApplication(Application):
    """
    Logger NOS-T Application.

    This object class defines the basic functionality for a NOS-T application
    that subscribes to a specified topic and logs all messages to file.

    Attributes:
        prefix (str): The test run namespace (prefix)
        simulator (:obj:`Simulator`): Application simulator defined in the *Simulator* class
        app_name (str): Logger application name (default: logger)
        app_description (str): Logger application description (optional)
        log_app (str): Application name to be logged (default: "+")
        log_topic (str): Topic to be logged (default: "#")
        log_dir (str): Directory to write log files (default: ".")
        log_file (:obj:`File`): Current log file
    """

    def __init__(self, app_name: str = "logger", app_description: str = None):
        """
        Initializes a new logging application.

        Args:
            app_name (str): application name (default: "logger")
            app_description (str): application description (optional)
        """
        super().__init__(app_name, app_description)
        self.log_topic = None
        self.log_app = None
        self.log_dir = None
        self.log_file = None

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
        log_app: str = "+",
        log_topic: str = "#",
        log_dir: str = ".",
    ) -> None:
        """
        Starts up the logger application by connecting to message broker,
        starting a background event loop, subscribing to manager events, and
        registering callback functions.

        Args:
            prefix (str): The test run namespace (prefix)
            config (:obj:`ConnectionConfig`): The connection configuration
            set_offset (bool): True, if the system clock offset shall be set
            time_status_step (:obj:`timedelta`): Time interval for status messages
            time_status_init (:obj:`datetime`): Initial time for status messages
            shut_down_when_terminated (bool): True, if the application shall shut down when terminated
            time_step (:obj:`timedelta`): Time step for the application
            manager_app_name (str): Manager application name
            log_app (str): Application name to be logged (default: "+")
            log_topic (str): Topic to be logged (default: "#")
            log_dir (str): Directory to write log files (default: ".")
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
                "logger_application",
                None,
            )
            self.set_offset = parameters.set_offset
            self.time_status_step = parameters.time_status_step
            self.time_status_init = parameters.time_status_init
            self.shut_down_when_terminated = parameters.shut_down_when_terminated

        self.log_app = log_app
        self.log_topic = log_topic
        self.log_dir = log_dir

        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Open log file now
        self._open_log_file()

        # Start up base application
        super().start_up(
            prefix,
            config,
            self.set_offset,
            self.time_status_step,
            self.time_status_init,
            self.shut_down_when_terminated,
        )

        # Add callback for specified topic(s)
        self.add_message_callback(self.log_app, self.log_topic, self.on_log_message)

        logger.info(f"Logger {self.app_name} started up and listening for messages.")

    def shut_down(self) -> None:
        """
        Shuts down the application by stopping the background event loop
        and disconnecting from the message broker.
        """
        # Close the log file if it's open
        self._close_log_file()

        # Shut down base application
        super().shut_down()

    def _open_log_file(self) -> None:
        """
        Opens a new log file for writing messages.
        """
        if self.log_file is not None:
            self._close_log_file()

        ts = (
            str(self.simulator.get_wallclock_time()).replace(" ", "T").replace(":", "-")
        )
        log_filename = os.path.join(self.log_dir, f"{ts}.log")
        self.log_file = open(log_filename, "a")
        self.log_file.write(f"Timestamp,Topic,Payload\n")
        logger.info(f"Logger {self.app_name} opened file {self.log_file.name}.")

    def _close_log_file(self) -> None:
        """
        Closes the current log file if it's open.
        """
        if self.log_file is not None:
            self.log_file.close()
            logger.info(f"Logger {self.app_name} closed file {self.log_file.name}.")
            self.log_file = None

    def on_log_message(self, ch, method, properties, body):
        """
        Callback function to log a message received by the logger application.

        Args:
            ch: The channel object
            method: The method frame
            properties: The message properties
            body: The message body
        """
        if self.log_file is not None:
            try:
                routing_key = method.routing_key
                payload = body.decode("utf-8") if isinstance(body, bytes) else str(body)

                logger.debug(f"Logger {self.app_name} logging message: {payload}")

                timestamp = self.simulator.get_wallclock_time()
                self.log_file.write(f"{timestamp},{routing_key},{payload}\n")
                self.log_file.flush()  # Ensure data is written immediately
            except Exception as e:
                logger.error(f"Error logging message: {e}")
        else:
            # If log file isn't open, try to reopen it
            self._open_log_file()
            logger.error(f"Logger {self.app_name} had to reopen log file.")
            # Try to log the message again
            self.on_log_message(ch, method, properties, body)
