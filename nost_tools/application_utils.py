"""
Provides utility classes to help applications interact with the broker.
"""

import logging
from typing import TYPE_CHECKING

import yaml
from dotenv import dotenv_values
from pydantic import ValidationError

from .observer import Observer
from .publisher import ScenarioTimeIntervalPublisher
from .schemas import Config, ModeStatus, TimeStatus
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
        rabbitmq_port (int): RabbitMQ broker port number
        keycloak_port (int): Keycloak IAM port number
        keycloak_realm (str): Keycloak realm name
        client_id (str): Keycloak client ID
        client_secret_key (str): Keycloak client secret key
        virtual_host (str): RabbitMQ virtual host
        is_tls (bool): True, if the connection uses Transport Layer Security (TLS)
        env_file (str): Path to the .env file
        yaml_file (str): Path to the YAML configuration file
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        host: str = None,
        rabbitmq_port: int = None,
        keycloak_port: int = None,
        keycloak_realm: str = None,
        client_id: str = None,
        client_secret_key: str = None,
        virtual_host: str = None,
        is_tls: bool = True,
        env_file: str = None,
        yaml_file: str = None,
    ):
        """
        Initializes a new connection configuration.

        Args:
            username (str): client username, provided by NOS-T operator
            password (str): client password, provided by NOS-T operator
            host (str): broker hostname
            rabbitmq_port (int): RabbitMQ broker port number
            keycloak_port (int): Keycloak IAM port number
            keycloak_realm (str): Keycloak realm name
            client_id (str): Keycloak client ID
            client_secret_key (str): Keycloak client secret key
            virtual_host (str): RabbitMQ virtual host
            is_tls (bool): True, if the connection uses TLS
            env_file (str): Path to the .env file
            yaml_file (str): Path to the YAML configuration file
        """
        self.yaml_config = None  # Initialize the attribute to store YAML data
        self.yaml_mode = (
            False  # Initialize the attribute to store the mode of operation
        )

        if env_file and yaml_file:
            logger.info(f"Loading configuration from {env_file} and {yaml_file}.")
            self.load_config_from_files(env_file, yaml_file)
            self.yaml_mode = True
        else:
            logger.info("Loading configuration from arguments.")
            self.username = username
            self.password = password
            self.host = host
            self.rabbitmq_port = rabbitmq_port
            self.keycloak_port = keycloak_port
            self.keycloak_realm = keycloak_realm
            self.client_id = client_id
            self.client_secret_key = client_secret_key
            self.virtual_host = virtual_host
            self.is_tls = is_tls

    def load_config_from_files(self, env_file: str, yaml_file: str):
        """
        Loads configuration from .env and YAML files.

        Args:
            env_file (str): Path to the .env file
            yaml_file (str): Path to the YAML configuration file
        """
        # Load .env file
        credentials = dotenv_values(env_file)
        self.username = credentials["USERNAME"]
        self.password = credentials["PASSWORD"]
        self.client_id = credentials["CLIENT_ID"]
        self.client_secret_key = credentials["CLIENT_SECRET_KEY"]

        # Load YAML file
        with open(yaml_file, "r") as file:
            yaml_data = yaml.safe_load(file)

        try:
            config = Config(**yaml_data)
            self.yaml_config = yaml_data
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")

        self.host = config.servers.rabbitmq.host
        self.rabbitmq_port = config.servers.rabbitmq.port
        self.keycloak_port = config.servers.keycloak.port
        self.keycloak_realm = config.servers.keycloak.realm
        self.virtual_host = config.servers.rabbitmq.virtual_host
        self.is_tls = config.servers.rabbitmq.tls and config.servers.keycloak.tls

        if not self.is_tls:
            raise ValueError("TLS must be enabled for both RabbitMQ and Keycloak.")


class ShutDownObserver(Observer):
    """
    Observer that shuts down an application after scenario termination.

    Attributes:
        app (:obj:`Application`): application to be shut down after termination
    """

    def __init__(self, app: "Application"):
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
            source (object): object that triggered a property change
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
        status = TimeStatus.model_validate(
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
            f"Sending time status {status.model_dump_json(by_alias=True,exclude_none=True)}."
        )

        self.app.send_message(
            app_name=self.app.app_name,
            app_topics="status.time",
            payload=status.model_dump_json(by_alias=True, exclude_none=True),
        )


class ModeStatusObserver(Observer):
    """
    Observer that publishes mode status messages for an application.

    Attributes:
        app (:obj:`Application`): application to publish mode status messages
    """

    def __init__(self, app: "Application"):
        """
        Initializes a new mode status observer.
        """
        self.app = app

    def stop_application(self):
        """
        Stops the application by closing the channel and connection if they are open.
        """
        if self.app.channel.is_open:
            self.app.channel.close()
            logger.info(f"Channel closed for application {self.app.app_name}.")

        if self.app.connection.is_open:
            self.app.connection.close()
            logger.info(f"Connection closed for application {self.app.app_name}.")

        logger.info(f'Application "{self.app.app_name}" successfully stopped.')

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Publishes a mode status message in response to a mode transition.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        if property_name == Simulator.PROPERTY_MODE:
            status = ModeStatus.model_validate(
                {
                    "name": self.app.app_name,
                    "description": self.app.app_description,
                    "properties": {"mode": self.app.simulator.get_mode()},
                }
            )
            logger.info(
                f"Sending mode status {status.model_dump_json(by_alias=True, exclude_none=True)}."
            )

            # Ensure self.prefix is a string
            if not isinstance(self.app.prefix, str):
                raise ValueError(f"Exchange ({self.app.prefix}) must be a string")

            # if self.app.channel.is_open and self.app.connection.is_open:
            self.app.send_message(
                app_name=self.app.app_name,
                app_topics="status.mode",
                payload=status.model_dump_json(by_alias=True, exclude_none=True),
            )
