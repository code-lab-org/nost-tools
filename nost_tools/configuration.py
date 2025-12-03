"""
Configuration Settings.
"""

import logging
import os

import yaml
from dotenv import find_dotenv, load_dotenv
from pydantic import ValidationError

from .errors import ConfigAssertionError, ConfigurationError, EnvironmentVariableError
from .schemas import (
    ChannelConfig,
    Config,
    Credentials,
    ExchangeConfig,
    ExecConfig,
    KeycloakConfig,
    RabbitMQConfig,
    RuntimeConfig,
    ServersConfig,
    SimulationConfig,
)

logger = logging.getLogger(__name__)


class ConnectionConfig:
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
        yaml_file (str): Path to the YAML configuration file
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        rabbitmq_host: str = None,
        rabbitmq_port: int = None,
        keycloak_authentication: bool = False,
        keycloak_host: str = None,
        keycloak_port: int = None,
        keycloak_realm: str = None,
        client_id: str = None,
        client_secret_key: str = None,
        virtual_host: str = None,
        is_tls: bool = True,
        yaml_file: str = None,
        app_name: str = None,
    ):
        """
        Initializes a new connection configuration.

        Args:
            username (str): client username, provided by NOS-T operator
            password (str): client password, provided by NOS-T operator
            host (str): broker hostname
            rabbitmq_port (int): RabbitMQ broker port number
            keycloak_authentication (bool): True, if Keycloak IAM authentication is used
            keycloak_port (int): Keycloak IAM port number
            keycloak_realm (str): Keycloak realm name
            client_id (str): Keycloak client ID
            client_secret_key (str): Keycloak client secret key
            virtual_host (str): RabbitMQ virtual host
            is_tls (bool): True, if the connection uses TLS
            yaml_file (str): Path to the YAML configuration file
            app_name (str): Name of the application to get specific configuration for
        """
        self.username = username
        self.password = password
        self.rabbitmq_host = rabbitmq_host
        self.keycloak_host = keycloak_host
        self.rabbitmq_port = rabbitmq_port
        self.keycloak_authentication = keycloak_authentication
        self.keycloak_port = keycloak_port
        self.keycloak_realm = keycloak_realm
        self.client_id = client_id
        self.client_secret_key = client_secret_key
        self.virtual_host = virtual_host
        self.is_tls = is_tls

        self.yaml_config = None
        self.predefined_exchanges_queues = False
        self.yaml_file = yaml_file
        self.unique_exchanges = {}
        self.channel_configs = []
        self.app_name = app_name
        self.app_specific = None

        self.create_connection_config()

    def get_exchanges(self):
        """
        Get exchanges from the YAML configuration file.
        """
        for app, app_channels in self.yaml_config.channels.items():
            for channel, details in app_channels.items():
                bindings = details.get("bindings", {}).get("amqp", {})
                exchange = bindings.get("exchange", {})
                exchange_name = exchange.get("name")
                if exchange_name:
                    exchange_config = ExchangeConfig(
                        name=exchange_name,
                        type=exchange.get("type", "topic"),
                        durable=exchange.get("durable", True),
                        auto_delete=exchange.get("autoDelete", False),
                        vhost=exchange.get("vhost", "/"),
                    )
                    if exchange_name in self.unique_exchanges:
                        if (
                            self.unique_exchanges[exchange_name]
                            != exchange_config.model_dump()
                        ):
                            raise ValueError(
                                f"Conflicting configurations for exchange '{exchange_name}': {self.unique_exchanges[exchange_name]} vs {exchange_config.model_dump()}"
                            )
                    else:
                        self.unique_exchanges[exchange_name] = (
                            exchange_config.model_dump()
                        )

    def get_channels(self):
        """
        Get channels from the YAML configuration file.
        """
        for app, app_channels in self.yaml_config.channels.items():
            for channel, details in app_channels.items():
                bindings = details.get("bindings", {}).get("amqp", {})
                exchange = bindings.get("exchange", {})
                exchange_name = exchange.get("name")
                address = details.get("address")
                if address and bindings:
                    channel_config = ChannelConfig(
                        app=app,
                        address=address,
                        exchange=exchange_name or "default_exchange",
                        durable=exchange.get("durable", True),
                        auto_delete=exchange.get("autoDelete", False),
                        vhost=exchange.get("vhost", "/"),
                    )
                    self.channel_configs.append(channel_config.model_dump())

    def get_exchanges_channels(self):
        """
        Get exchanges and channels from the YAML configuration file.
        """

        self.get_exchanges(), self.get_channels()
        if self.unique_exchanges and self.channel_configs:
            self.predefined_exchanges_queues = True
        self.simulation_config = SimulationConfig(
            exchanges=self.unique_exchanges,
            queues=self.channel_configs,
            execution_parameters=self.yaml_config.execution,
            predefined_exchanges_queues=self.predefined_exchanges_queues,
        )

    def load_environment_variables(self):
        """
        Loads an environment (.env) file and returns the parsed data.
        """
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            logger.info(f"Checking for credentials in the .env file: {dotenv_path}.")
            load_dotenv(dotenv_path, override=True)
        else:
            logger.warning(
                "Checking for credentials in the system environment variables."
            )
        # Load credentials from environment variables
        # For Keycloak authentication, we support two modes:
        # 1. User account: USERNAME + PASSWORD + CLIENT_ID + CLIENT_SECRET_KEY
        # 2. Service account: CLIENT_ID + CLIENT_SECRET_KEY only
        if self.server_config.servers.rabbitmq.keycloak_authentication:
            env_data = {
                "USERNAME": os.getenv("USERNAME"),
                "PASSWORD": os.getenv("PASSWORD"),
                "CLIENT_ID": os.getenv("CLIENT_ID"),
                "CLIENT_SECRET_KEY": os.getenv("CLIENT_SECRET_KEY"),
            }
        else:
            # Non-Keycloak authentication requires username and password
            env_data = {
                "USERNAME": os.getenv("USERNAME"),
                "PASSWORD": os.getenv("PASSWORD"),
            }
            # Check required fields for non-Keycloak auth
            missing_fields = [field for field, value in env_data.items() if value is None]
            if missing_fields:
                raise EnvironmentVariableError(
                    f"Missing required fields in .env file: {', '.join(missing_fields)}"
                )

        try:
            if self.server_config.servers.rabbitmq.keycloak_authentication:
                # Let Credentials validator handle authentication mode detection and validation
                self.credentials_config = Credentials(
                    username=env_data.get("USERNAME"),
                    password=env_data.get("PASSWORD"),
                    client_id=env_data.get("CLIENT_ID"),
                    client_secret_key=env_data.get("CLIENT_SECRET_KEY"),
                )
            else:
                self.credentials_config = Credentials(
                    username=env_data["USERNAME"],
                    password=env_data["PASSWORD"],
                )
        except ValidationError as err:
            raise EnvironmentVariableError(f"Invalid environment variables: {err}")

    def get_app_specific_config(self, app_name, app_type="managed_applications"):
        """
        Get application-specific configuration from execution.managed_applications or execution.applications if available.

        Args:
            app_name (str): Name of the application
            app_type (str): Type of application - "managed_applications" or "applications" (default: "managed_applications")

        Returns:
            dict: Application-specific configuration parameters if available, otherwise None.
        """
        if not os.path.exists(self.yaml_file):
            raise ConfigurationError("Couldn't load config file (not found)")

        with open(self.yaml_file, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

            try:
                return yaml_data["execution"][app_type][app_name][
                    "configuration_parameters"
                ]
            except:
                return None

    def load_yaml_config_file(self):
        """
        Loads a YAML configuration file and returns the parsed data.
        """
        if not os.path.exists(self.yaml_file):
            raise ConfigurationError("Couldn't load config file (not found)")

        with open(self.yaml_file, "r", encoding="utf-8") as f:
            try:
                yaml_data = yaml.safe_load(f)  # Store the parsed YAML data
            except yaml.YAMLError as err:
                raise ConfigurationError(f"Invalid YAML configuration: {err}")

        try:
            self.yaml_config = Config(**yaml_data)
        except ValidationError as err:
            raise ConfigurationError(f"Invalid configuration: {err}")

    def create_connection_config(self):
        """
        Creates a connection configuration.
        """
        if self.yaml_file:
            try:
                self.load_yaml_config_file()
            except ConfigurationError as e:
                raise ValueError(f"Configuration error: {e}")

            try:
                assert all(
                    item in self.yaml_config.execution.required_apps
                    for item in self.yaml_config.channels.keys()
                ), "Application names do not match the channels defined in the configuration file."
            except ConfigAssertionError as e:
                raise ValueError(f"Assertion error: {e}")
            # Load app-specific configuration if app_name is provided
            if self.app_name:
                # Try applications section first, then managed_applications
                self.app_specific = self.get_app_specific_config(self.app_name, app_type="applications")
                if not self.app_specific:
                    self.app_specific = self.get_app_specific_config(self.app_name, app_type="managed_applications")
        else:
            try:
                self.yaml_config = Config(
                    servers=ServersConfig(
                        rabbitmq=RabbitMQConfig(
                            host=self.rabbitmq_host,
                            port=self.rabbitmq_port,
                            virtual_host=self.virtual_host,
                            tls=self.is_tls,
                            keycloak_authentication=self.keycloak_authentication,
                        ),
                        keycloak=KeycloakConfig(
                            host=self.keycloak_host,
                            port=self.keycloak_port,
                            realm=self.keycloak_realm,
                            tls=self.is_tls,
                        ),
                    ),
                    channels={},
                    execution=ExecConfig(),
                )
            except:
                self.yaml_config = Config(
                    servers=ServersConfig(
                        rabbitmq=RabbitMQConfig(), keycloak=KeycloakConfig()
                    ),
                    channels={},
                    execution=ExecConfig(),
                )

        self.get_exchanges_channels()

        server_config = self.yaml_config.copy()
        if hasattr(server_config, "channels"):
            del server_config.channels
        if hasattr(server_config, "execution"):
            del server_config.execution
        self.server_config = server_config

        if self.username is not None and self.password is not None:
            logger.info("Using user-provided credentials.")
            self.credentials_config = Credentials(
                username=self.username,
                password=self.password,
                client_id=self.client_id,
                client_secret_key=self.client_secret_key,
            )
        else:
            self.load_environment_variables()

        self.rc = RuntimeConfig(
            credentials=self.credentials_config,
            server_configuration=server_config,
            simulation_configuration=self.simulation_config,
            application_configuration=self.app_specific,
            yaml_file=self.yaml_file,
        )
