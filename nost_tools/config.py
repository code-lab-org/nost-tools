"""
Configuration Settings.
"""

import os
from typing import Dict, List

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class RabbitMQConfig(BaseModel):
    host: str = Field("localhost", description="RabbitMQ host.")
    port: int = Field(5672, description="RabbitMQ port.")
    virtual_host: str = Field("/", description="RabbitMQ virtual host.")
    tls: bool = Field(False, description="RabbitMQ TLS.")


class KeycloakConfig(BaseModel):
    host: str = Field("localhost", description="Keycloak host.")
    port: int = Field(8080, description="Keycloak port.")
    realm: str = Field("master", description="Keycloak realm.")
    tls: bool = Field(False, description="Keycloak TLS.")


class ServersConfig(BaseModel):
    rabbitmq: RabbitMQConfig = Field(..., description="RabbitMQ configuration.")
    keycloak: KeycloakConfig = Field(..., description="Keycloak configuration.")


class ExecConfig(BaseModel):
    timescale: int = Field(
        60,
        description="Execution timescale. For example, if the timescale is 60, 1 wallclock second is equivalent to 60 simulation seconds.",
    )
    prefix: str = Field(
        "nost",
        description="Execution prefix. This is used as the RabbitMQ exchange throughout the entire execution.",
    )
    application_names: List[str] = Field(
        ["manager", "managed_application"],
        description="List of all application names involved in execution.",
    )


class Config(BaseModel):
    servers: ServersConfig = Field(..., description="Servers configuration.")
    channels: Dict[str, Dict] = Field({}, description="Channels configuration.")
    execution: ExecConfig = Field(..., description="Applications configuration.")


class ExchangeConfig(BaseModel):
    name: str
    type: str = "topic"
    durable: bool = True
    auto_delete: bool = False
    vhost: str = "/"


class ChannelConfig(BaseModel):
    app: str
    address: str
    exchange: str
    durable: bool
    auto_delete: bool
    vhost: str


class Credentials(BaseModel):
    username: str = Field(..., description="Username for authentication.")
    password: str = Field(..., description="Password for authentication.")
    client_id: str = Field(..., description="Client ID for authentication.")
    client_secret_key: str = Field(
        ..., description="Client secret key for authentication."
    )


class SimulationConfig(BaseModel):
    exchanges: Dict[str, Dict] = Field(
        default_factory=dict, description="Dictionary of exchanges."
    )
    queues: List[Dict] = Field(default_factory=list, description="List of channels.")
    execution_parameters: ExecConfig = Field(..., description="Execution parameters.")
    predefined_exchanges_queues: bool = Field(
        False, description="Predefined exchanges and queues."
    )


class RuntimeConfig(BaseModel):
    credentials: Credentials = Field(..., description="Credentials for authentication.")
    server_configuration: Config = (
        Field(..., description="Simulation configuration."),
    )
    simulation_configuration: SimulationConfig = Field(
        ..., description="Simulation configuration."
    )


class ConfigurationError(Exception):
    """Configuration error"""


class EnvironmentVariableError(Exception):
    """Environment variable error"""


class AssertionError(Exception):
    """Assertion error"""


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
        self.yaml_config = None
        self.yaml_mode = False

        self.predefined_exchanges_queues = False
        self.env_file = env_file
        self.yaml_file = yaml_file
        self.unique_exchanges = {}
        self.channel_configs = []

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

    def load_env_file(self) -> Credentials:
        """
        Loads an environment (.env) file and returns the parsed data.
        """
        if not os.path.exists(self.env_file):
            raise EnvironmentVariableError("Couldn't load .env file (file not found)")

        load_dotenv(dotenv_path=self.env_file)

        required_fields = ["USERNAME", "PASSWORD", "CLIENT_ID", "CLIENT_SECRET_KEY"]
        env_data = {field: os.getenv(field) for field in required_fields}

        missing_fields = [field for field, value in env_data.items() if value is None]
        if missing_fields:
            raise EnvironmentVariableError(
                f"Missing required fields in .env file: {', '.join(missing_fields)}"
            )

        try:
            self.credentials_config = Credentials(
                username=env_data["USERNAME"],
                password=env_data["PASSWORD"],
                client_id=env_data["CLIENT_ID"],
                client_secret_key=env_data["CLIENT_SECRET_KEY"],
            )
        except ValidationError as err:
            raise EnvironmentVariableError(f"Invalid environment variables: {err}")

    def load_yaml_config_file(self) -> Config:
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

        if self.env_file:
            try:
                self.load_env_file()
            except EnvironmentVariableError as e:
                raise ValueError(f"Environment variable error: {e}")
        else:
            self.credentials_config = Credentials(
                username=self.username,
                password=self.password,
                client_id=self.client_id,
                client_secret_key=self.client_secret_key,
            )

        if self.yaml_file:
            try:
                self.load_yaml_config_file()
            except ConfigurationError as e:
                raise ValueError(f"Configuration error: {e}")

            try:
                assert all(
                    item in self.yaml_config.execution.application_names
                    for item in self.yaml_config.channels.keys()
                ), "Application names do not match the channels defined in the configuration file."
            except AssertionError as e:
                raise ValueError(f"Assertion error: {e}")
        else:
            try:
                self.yaml_config = Config(
                    servers=ServersConfig(
                        rabbitmq=RabbitMQConfig(
                            host=self.host,
                            port=self.rabbitmq_port,
                            virtual_host=self.virtual_host,
                            tls=self.is_tls,
                        ),
                        keycloak=KeycloakConfig(
                            host=self.host,
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

        self.rc = RuntimeConfig(
            credentials=self.credentials_config,
            server_configuration=server_config,
            simulation_configuration=self.simulation_config,
        )
