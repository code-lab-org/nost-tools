import logging
import os
import threading

from .application import Application
from .schemas import InitCommand, StartCommand, StopCommand, UpdateCommand

logger = logging.getLogger(__name__)


class LoggerApplication(Application):
    """
    Logger NOS-T Application.

    This object class defines the basic functionality for a NOS-T application
    that subscribes to a specified topic and logs all messages to file.

    Attributes:
        prefix (str) : The test run namespace (prefix)\n
        simulator (:obj:`Simulator`): Application simulator defined in the *Simulator* class
        client (:obj:`Client`): Application MQTT client
        app_name (str): Logger application name (default: logger)\n
        app_description (str): Logger application description (optional)\n
        log_app (str): Application name to be logged (default: "+")\n
        log_topic (str): Topic to be logged (default: "#")\n
        log_dir (str): Directory to write log files (default: ".")\n
        log_file (:obj:`File`): Current log file
    """

    def __init__(self, app_name="logger", app_description=None):
        super().__init__(app_name, app_description)
        self.log_topic = None
        self.log_app = None
        self.log_dir = None
        self.log_file = None

    def start_up(
        self, prefix, config, set_offset=True, log_app="+", log_topic="#", log_dir=".",
    ):
        """
        Starts up the logger application by connecting to message broker,
        starting a background event loop, subscribing to manager events, and
        registering callback functions.

        Args:
            prefix (str): The test run namespace (prefix)\n
            config (:obj:`ConnectionConfig`): The connection configuration
            set_offset (bool): True, if the system clock offset shall be set
        """
        self.log_app = log_app
        self.log_topic = log_topic
        self.log_dir = log_dir
        self.client.on_connect = self.on_log_connect
        self.client.on_disconnect = self.on_log_disconnect
        # start up base application
        super().start_up(prefix, config, set_offset)
        # add callback for specified topic(s)
        self.add_message_callback(self.log_app, self.log_topic, self.on_log_message)

    def shut_down(self):
        """
            Shuts down the application by stopping the background event loop
            and disconnecting from the message broker.
        """
        # unregister callback functions
        self.remove_message_callback(self.log_app, self.log_topic)
        # shut down base application
        super().shut_down()

    def on_log_connect(self, client, userdata, flags, rc):
        """
        on_log_connect is a callback function that opens the log file when
        the MQTT client connects to the broker.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            flags (dict): Response flags sent by the broker
            rc (int): The connection result
        """
        if self.log_file is not None:
            self.log_file().close()
            self.log_file = None
        ts = (
            str(self.simulator.get_wallclock_time()).replace(" ", "T").replace(":", "-")
        )
        self.log_file = open(os.path.join(self.log_dir, f"{ts}.log"), "a")
        self.log_file.write(f"Timestamp,Topic,Payload\n")
        logger.info(f"Logger {self.app_name} opened file {self.log_file.name}.")

    def on_log_disconnect(self, client, userdata, rc):
        """
        on_log_disconnect is a callback function that closes the log file when
        the MQTT client disconnects from the broker.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            rc (int): The connection result
        """
        if self.log_file is not None:
            self.log_file.close()
            logger.info(f"Logger {self.app_name} closed file {self.log_file.name}.")
            self.log_file = None

    def on_log_message(self, client, userdata, message):
        """
        on_log_message is a callback function to log a message received by
        the logger application.

        Args:
            client (:obj:`Client`): The client instance for this callback
            userdata (obj): The private user data as set in the client
            message (:obj:`MQTTMessage`): The MQTT message
        """
        if self.log_file is not None:
            logger.debug(f"Logger {self.app_name} logging message {message.payload}.")
            self.log_file.write(
                f"{self.simulator.get_wallclock_time()},{message.topic},{message.payload}\n"
            )
        else:
            logger.error(f"Logger {self.app_name} cannot log: no file open.")
