"""
Provides utility classes to help applications interact with the broker.

@author: Paul T. Grogan <pgrogan@stevens.edu>
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from .observer import Observer
from .publisher import ScenarioTimeIntervalPublisher
from .schemas import ModeStatus, TimeStatus
from .simulator import Mode, Simulator

if TYPE_CHECKING:
    from .application import Application

logger = logging.getLogger(__name__)


class ConnectionConfig(object):
    """Connection configuration.

    The configuration settings to establish a connection to the broker, including authentication for the
    user and identification of the server.

    Attributes:
        username (str): client username, provided by NOS-T operator
        password (str): client password, provided by NOS-T operator
        host (str): broker hostname
        port (int): broker port number
        is_tls (bool): True, if the connection uses TLS (Transport Layer Security)
    """

    def __init__(
        self, username: str, password: str, host: str, port: int, ca_list: str, cert: str, key: str, is_tls: bool = True
    ):
        """
        Initializes a new connection configuration.

        Args:
            username (str): client username
            password (str): client password
            host (str): broker hostname
            port (int): broker port number
            is_tls (bool): True, if the connection uses Transport Layer Security
        """
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.ca_list = ca_list
        self.cert = cert
        self.key = key
        self.is_tls = is_tls


class ShutDownObserver(Observer):
    """
    Observer that shuts down an application after scenario termination.

    Attributes:
        app (:obj:`Application`): application to be shut down after termination
    """

    def __init__(
        self, app: Application
    ):
        """
        Initializes a new shut down observer.

        Args:
            app (:obj:`Application`): application to be shut down after termination
        """
        self.app = app

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Shuts down the application in response to a transition to the TERMINATED mode.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.TERMINATED:
            self.app.shut_down()


class TimeStatusPublisher(ScenarioTimeIntervalPublisher):
    """
    Publishes time status messages for an application at a regular interval.

    Attributes:
        app (:obj:`Application`): application to publish time status messages
    """

    def publish_message(self) -> None:
        """
        Publishes a time status message.
        """
        status = TimeStatus.parse_obj(
            {
                "name": self.app.app_name,
                "description": self.app.app_description,
                "properties": {
                    "simTime": self.app.simulator.get_time(),
                    "time": self.app.simulator.get_wallclock_time(),
                },
            }
        )
        logger.info(
            f"Sending time status {status.json(by_alias=True,exclude_none=True)}."
        )
        # publish time status message
        self.app.client.publish(
            f"{self.app.prefix}/{self.app.app_name}/status/time",
            status.json(by_alias=True, exclude_none=True),
        )


class ModeStatusObserver(Observer):
    """
    Observer that publishes mode status messages for an application.

    Attributes:
        app (:obj:`Application`): application to publish mode status messages
    """

    def __init__(
        self, app: Application
    ):
        """
        Initializes a new mode status observer.
        """
        self.app = app

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Publishes a mode status message in response ot a mode transition.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        if property_name == Simulator.PROPERTY_MODE:
            status = ModeStatus.parse_obj(
                {
                    "name": self.app.app_name,
                    "description": self.app.app_description,
                    "properties": {"mode": self.app.simulator.get_mode()},
                }
            )
            logger.info(
                f"Sending mode status {status.json(by_alias=True,exclude_none=True)}."
            )
            self.app.client.publish(
                f"{self.app.prefix}/{self.app.app_name}/status/mode",
                status.json(by_alias=True, exclude_none=True),
            )
