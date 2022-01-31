import logging

from .observer import Observer
from .publisher import ScenarioTimeIntervalPublisher
from .schemas import ModeStatus, TimeStatus
from .simulator import Mode, Simulator

logger = logging.getLogger(__name__)


class ConnectionConfig(object):
    """Connection configuration.

    The configuration settings to establish a connection to the broker, including authentication for the
    user and identification of the server.

    Args:
        username (str): The client username, provided by NOS-T operator
        password (str): The client password, provided by NOS-T operator
        host (str): The server hostname
        port (int): The server port number
        is_tls (bool): True, if the connection uses TLS (Transport Layer Security)

    Attributes:
        username (str): The client username, provided by NOS-T operator
        password (str): The client password, provided by NOS-T operator
        host (str): The server hostname.
        port (int): The server port number.
        is_tls (bool): True, if the connection uses TLS (Transport Layer Security)
    """

    def __init__(self, username, password, host, port, is_tls=True):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.is_tls = is_tls


class ShutDownObserver(Observer):
    """
    This method shuts down an application after the simulation is terminated.

    Attributes:
        app (:obj:`Application`): The application that will be terminated by the simulation
    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        on_change creates a callback to the application, essentially creating an alert that one of the application's properties
        is being changed by another function. It notes the observable that made the change, the name of the changed property, the
        value before the change, and the value after the change.

        Args:
            source (:obj:`Observable`): The observervable that triggered the change.
            property_name (str): The name of property that is changing.
            old_value (obj): The old value of the named property.
            new_value (obj): The new value of the named property.
        """
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.TERMINATED:
            self.app.shut_down()


class TimeStatusPublisher(ScenarioTimeIntervalPublisher):
    """
    Publishes time status messages at a regular interval (scenario time). The interval is provided by the scenario start message
    and will begin at the time indicated by the scenario.

    Attributes:
        app (:obj:`Application`): The application that will be publishing time status messages
    """

    def publish_message(self):
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
        app (:obj:`Application`): The application that will be publishing mode status messages
    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
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
