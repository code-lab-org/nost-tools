"""
Provides a base application that publishes messages from a simulator to a broker.
"""

from datetime import datetime, timedelta
import logging
import ntplib
import paho.mqtt.client as mqtt
import ssl
import time
from typing import Callable

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
        self.client.publish(
            f"{self.prefix}/{self.app_name}/status/ready",
            status.json(by_alias=True, exclude_none=True),
        )

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
        # maybe configure wallclock offset
        if set_offset:
            self.set_wallclock_offset()
        # set test run prefix
        self.prefix = prefix
        # set client username and password
        # self.client.username_pw_set(username=config.username, password=config.password)
        # maybe configure transport layer security (encryption)
        if config.is_tls:
            self.client.tls_set(ca_certs=config.ca_list, certfile=config.cert, keyfile=config.key)
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
        topic = f"{self.prefix}/{self.app_name}/{app_topic}"
        logger.info(f"Publishing to topic {topic}: {payload}")
        self.client.publish(topic, payload)

    def add_message_callback(
        self, app_name: str, app_topic: str, callback: Callable
    ) -> None:
        """
        Adds a message callback bound to an application name and topic `prefix/app_name/app_topic`.

        Args:
            app_name (str): application name
            app_topic (str): application topic
            callback (Callable): callback function
        """
        topic = f"{self.prefix}/{app_name}/{app_topic}"
        logger.debug(f"Subscribing and adding callback to topic: {topic}")
        self.client.subscribe(topic)
        self.client.message_callback_add(topic, callback)

    def remove_message_callback(self, app_name: str, app_topic: str) -> None:
        """
        Removes a message callback for application name and topic `prefix/app_name/app_topic`.

        Args:
            app_name (str): The application name
            app_topic (str): The application topic
        """
        topic = f"{self.prefix}/{app_name}/{app_topic}"
        logger.debug(f"Removing callback from topic: {topic}")
        self.client.message_callback_remove(topic)

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
