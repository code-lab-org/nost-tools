from datetime import timedelta
import logging
import ntplib
import paho.mqtt.client as mqtt
import time

from .schemas import ReadyStatus
from .simulator import Simulator
from .application_utils import TimeStatusPublisher, ModeStatusObserver, ShutDownObserver

logger = logging.getLogger(__name__)


class Application(object):
    """
    A template of an NOS-T Application.

    This object class defines the main functionality of a NOS-T application. The attributes of this class create a replicable
    object that can be modified for user needs.

    Attributes:
        prefix (str) : The test run namespace (prefix)\n
        simulator (:obj:`Simulator`): Application simulator -- calls on the simulator.py class for functionality
        client (:obj:`Client`): Application MQTT client
        app_name (str): Test run application name
        app_description (str): Test run application description (optional)\n
        time_status_step (:obj:`timedelta`): Scenario duration between time status messages
        time_status_init (:obj:`datetime`): Scenario time of first time status message
    """

    def __init__(self, app_name, app_description=None):
        self.simulator = Simulator()
        self.client = mqtt.Client()
        self.prefix = None
        self.app_name = app_name
        self.app_description = app_description
        self._time_status_publisher = None
        self._mode_status_observer = None
        self._shut_down_observer = None

    def ready(self):
        """
        ready function defines the application's readiness upon connection. It sends the ready
        status message indicating this application is prepared to enter the simulation.
        """
        # publish ready status message
        status = ReadyStatus.parse_obj(
            {
                "name": self.app_name,
                "description": self.app_description,
                "properties": {"ready": True},
            }
        )
        self.client.publish(
            f"{self.prefix}/{self.app_name}/status/ready",
            status.json(by_alias=True, exclude_none=True),
        )

    def start_up(
        self,
        prefix,
        config,
        set_offset=True,
        time_status_step=None,
        time_status_init=None,
        shut_down_when_terminated=False,
    ):
        """
        start_up starts up the application to prepare it for entering the simulation.
        Connects to the message broker and starts a background event loop by establishing the simulation prefix,
        the connection configuration, and the intervals for publishing time status messages.

        Args:
            prefix (str) : The test run namespace (prefix)\n
            config (:obj:`ConnectionConfig`) : The connection configuration
            set_offset (bool) : True, if the system clock offset shall be set
            time_status_step (:obj:`timedelta`): Scenario duration between time status messages
            time_status_init (:obj:`datetime`): Scenario time for first time status message
            shut_down_when_terminated (bool) : True, if the application should shut down when the simulation is terminated
        """
        # maybe configure wallclock offset
        if set_offset:
            self.set_wallclock_offset()
        # set test run prefix
        self.prefix = prefix
        # set client username and password
        self.client.username_pw_set(username=config.username, password=config.password)
        # maybe configure transport layer security (encryption)
        if config.is_tls:
            self.client.tls_set()
        # connect to server
        self.client.connect(config.host, config.port)
        # configure observers
        self._create_time_status_publisher(time_status_step, time_status_init)
        self._create_mode_status_observer()
        if shut_down_when_terminated:
            self._create_shut_down_observer()
        # start background loop
        self.client.loop_start()
        logger.info(f"Application {self.app_name} successfully started up.")

    def _create_time_status_publisher(self, time_status_step, time_status_init):
        """
        _create_time_status_publisher creates a new time status publisher, using the publisher class to publish the
        time status for the reference application ('self') if the arguments are provided.

        Args:
            time_status_step (:obj:`timedelta`): Scenario duration between time status messages
            time_status_init (:obj:`datetime`): Scenario time for first time status message
        """
        if time_status_step is not None:
            if self._time_status_publisher is not None:
                self.simulator.remove_observer(self._time_status_publisher)
            self._time_status_publisher = TimeStatusPublisher(
                self, time_status_step, time_status_init
            )
            self.simulator.add_observer(self._time_status_publisher)

    def _create_mode_status_observer(self):
        """
        _create_mode_status_observer creates a new mode status observer to publish the
        mode status for the reference application ('self').
        """
        if self._mode_status_observer is not None:
            self.simulator.remove_observer(self._mode_status_observer)
        self._mode_status_observer = ModeStatusObserver(self)
        self.simulator.add_observer(self._mode_status_observer)

    def _create_shut_down_observer(self):
        """
        _create_shut_down_observer creates a new observer to shut down the
        application when the simulation is terminated.
        """
        if self._shut_down_observer is not None:
            self.simulator.remove_observer(self._shut_down_observer)
        self._shut_down_observer = ShutDownObserver(self)
        self.simulator.add_observer(self._shut_down_observer)

    def shut_down(self):
        """
        shut_down shuts down the application by stopping the background event loop, and also disconnects
        the application from the message broker.
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

    def send_message(self, app_topic, payload):
        """
        send_message sends a message. Helper function to publish
        a message with payload `payload` to the topic `prefix/app_name/app_topic`.

        Args:
            app_topic (str) : The application-specific topic
            payload (str) : The message payload (JSON-encoded string)

        """
        topic = f"{self.prefix}/{self.app_name}/{app_topic}"
        logger.info(f"Publishing to topic {topic} : {payload}")
        self.client.publish(topic, payload)

    def add_message_callback(self, app_name, app_topic, callback):
        """
        add_message_callback adds a message callback. Helper function to add a callback
        to a message topic in the format `prefix/app_name/app_topic`.

        Args:
            app_name (str) : The application name
            app_topic (str) : The application topic
            callback (fun) : The callback function
        """
        topic = f"{self.prefix}/{app_name}/{app_topic}"
        logger.debug(f"Subscribing and adding callback to topic: {topic}")
        self.client.subscribe(topic)
        self.client.message_callback_add(topic, callback)

    def remove_message_callback(self, app_name, app_topic):
        """
        remove_message_callback removes a message callback. Helper function to remove a callback
        from a message topic in the format `prefix/app_name/app_topic`.

        Args:
            app_name (str) : The application name
            app_topic (str) : The application topic
        """
        topic = f"{self.prefix}/{app_name}/{app_topic}"
        logger.debug(f"Removing callback from topic: {topic}")
        self.client.message_callback_remove(topic)

    def set_wallclock_offset(self, host="pool.ntp.org", retry_delay_s=5, max_retry=5):
        """
        set_wallclock_offset contacts an NTP server to determine the system clock offset. If optional set_offset included in start_up function call,
        saves the offset value to account for time differences between applications for synchronization.

        Args:
            host (str) : The NTP host (default: 'pool.ntp.org')\n
            retry_delay_s (int) : The number of seconds to wait before retrying
            max_retry (int) : The maximum number of retries allowed
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
