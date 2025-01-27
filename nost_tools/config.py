"""
Configuration Settings.
"""

import os
from typing import Dict, List, Optional

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


# class RuntimeConfig(BaseModel):
#     username: str = Field(..., description="Username for authentication.")
#     password: str = Field(..., description="Password for authentication.")
#     client_id: str = Field(..., description="Client ID for authentication.")
#     client_secret_key: str = Field(
#         ..., description="Client secret key for authentication."
#     )
#     host: str = Field(..., description="RabbitMQ host.")
#     rabbitmq_port: int = Field(..., description="RabbitMQ port.")
#     keycloak_port: int = Field(..., description="Keycloak port.")
#     keycloak_realm: str = Field(..., description="Keycloak realm.")
#     virtual_host: str = Field(..., description="RabbitMQ virtual host.")
#     is_tls: bool = Field(
#         ..., description="TLS must be enabled for both RabbitMQ and Keycloak."
#     )
#     exchanges: Dict[str, Dict] = Field(
#         default_factory=dict, description="Dictionary of exchanges."
#     )
#     channels: List[Dict] = Field(default_factory=list, description="List of channels.")
#     predefined_exchanges_queues: bool = Field(
#         False, description="Predefined exchanges and queues."
#     )


class RuntimeConfigUpdate(BaseModel):
    credentials: Credentials = Field(..., description="Credentials for authentication.")
    simulation_configuration: Config = (
        Field(..., description="Simulation configuration."),
    )
    exchanges: Dict[str, Dict] = Field(
        default_factory=dict, description="Dictionary of exchanges."
    )
    channels: List[Dict] = Field(default_factory=list, description="List of channels.")
    predefined_exchanges_queues: bool = Field(
        False, description="Predefined exchanges and queues."
    )


class ConfigurationError(Exception):
    """Configuration error"""


class EnvironmentVariableError(Exception):
    """Environment variable error"""


class AssertionError(Exception):
    """Assertion error"""


def get_exchanges(config: Config) -> Dict[str, Dict]:
    unique_exchanges = {}

    for app, app_channels in config.channels.items():
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
                if exchange_name in unique_exchanges:
                    if unique_exchanges[exchange_name] != exchange_config.model_dump():
                        raise ValueError(
                            f"Conflicting configurations for exchange '{exchange_name}': {unique_exchanges[exchange_name]} vs {exchange_config.model_dump()}"
                        )
                else:
                    unique_exchanges[exchange_name] = exchange_config.model_dump()

    return unique_exchanges


def get_channels(config: Config) -> List[Dict]:
    channel_configs = []

    for app, app_channels in config.channels.items():
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
                channel_configs.append(channel_config.model_dump())

    return channel_configs


def load_env_file(file_path: str) -> Credentials:
    """
    Loads an environment (.env) file and returns the parsed data.

    Args:
        file_path (str): Path to the .env file.

    Returns:
        Credentials: Parsed environment data.
    """
    if not os.path.exists(file_path):
        raise EnvironmentVariableError("Couldn't load .env file (file not found)")

    load_dotenv(dotenv_path=file_path)

    required_fields = ["USERNAME", "PASSWORD", "CLIENT_ID", "CLIENT_SECRET_KEY"]
    env_data = {field: os.getenv(field) for field in required_fields}

    missing_fields = [field for field, value in env_data.items() if value is None]
    if missing_fields:
        raise EnvironmentVariableError(
            f"Missing required fields in .env file: {', '.join(missing_fields)}"
        )

    try:
        return Credentials(
            username=env_data["USERNAME"],
            password=env_data["PASSWORD"],
            client_id=env_data["CLIENT_ID"],
            client_secret_key=env_data["CLIENT_SECRET_KEY"],
        )
    except ValidationError as err:
        raise EnvironmentVariableError(f"Invalid environment variables: {err}")


def load_yaml_config_file(file_path: str) -> Config:
    """
    Loads a YAML configuration file and returns the parsed data.

    Args:
        file_path (str): Path to the YAML configuration file.

    Returns:
        Config: Parsed YAML data.
    """
    if not os.path.exists(file_path):
        raise ConfigurationError("Couldn't load config file (not found)")

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            yaml_data = yaml.safe_load(f)  # Store the parsed YAML data
        except yaml.YAMLError as err:
            raise ConfigurationError(f"Invalid YAML configuration: {err}")

    try:
        return Config(**yaml_data)
    except ValidationError as err:
        raise ConfigurationError(f"Invalid configuration: {err}")


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
        self.yaml_config = None  # Initialize the attribute to store YAML data
        self.config = None  # Initialize config to None
        self.yaml_mode = (
            False  # Initialize the attribute to store the mode of operation
        )
        self.predefined_exchanges_queues = False

        if env_file:
            try:
                credentials = load_env_file(env_file)
            except EnvironmentVariableError as e:
                raise ValueError(f"Environment variable error: {e}")
        else:
            credentials = Credentials(
                username=username,
                password=password,
                client_id=client_id,
                client_secret_key=client_secret_key,
            )

        if yaml_file:
            try:
                yaml_config = load_yaml_config_file(yaml_file)
            except ConfigurationError as e:
                raise ValueError(f"Configuration error: {e}")

            try:
                assert all(
                    item in yaml_config.execution.application_names
                    for item in yaml_config.channels.keys()
                ), "Application names do not match the channels defined in the configuration file."
            except AssertionError as e:
                raise ValueError(f"Assertion error: {e}")
        else:
            try:
                yaml_config = Config(
                    servers=ServersConfig(
                        rabbitmq=RabbitMQConfig(
                            host=host,
                            port=rabbitmq_port,
                            virtual_host=virtual_host,
                            tls=is_tls,
                        ),
                        keycloak=KeycloakConfig(
                            host=host,
                            port=keycloak_port,
                            realm=keycloak_realm,
                            tls=is_tls,
                        ),
                    ),
                    channels={},
                    execution=ExecConfig(),
                )
            except:
                yaml_config = Config(
                    servers=ServersConfig(
                        rabbitmq=RabbitMQConfig(), keycloak=KeycloakConfig()
                    ),
                    channels={},
                    execution=ExecConfig(),
                )

        unique_exchanges, channel_configs = get_exchanges(yaml_config), get_channels(
            yaml_config
        )

        if unique_exchanges and channel_configs:
            self.predefined_exchanges_queues = True
            self.config = yaml_config

        # self.rc = RuntimeConfig(
        #     username=credentials.username,
        #     password=credentials.password,
        #     client_id=credentials.client_id,
        #     client_secret_key=credentials.client_secret_key,
        #     host=yaml_config.servers.rabbitmq.host,
        #     rabbitmq_port=yaml_config.servers.rabbitmq.port,
        #     keycloak_port=yaml_config.servers.keycloak.port,
        #     keycloak_realm=yaml_config.servers.keycloak.realm,
        #     virtual_host=yaml_config.servers.rabbitmq.virtual_host,
        #     is_tls=yaml_config.servers.rabbitmq.tls
        #     and yaml_config.servers.keycloak.tls,
        #     exchanges=unique_exchanges,
        #     channels=channel_configs,
        #     predefined_exchanges_queues=self.predefined_exchanges_queues,
        # )

        self.rc = RuntimeConfigUpdate(
            credentials=credentials,
            simulation_configuration=yaml_config,
            exchanges=unique_exchanges,
            channels=channel_configs,
            predefined_exchanges_queues=self.predefined_exchanges_queues,
        )


def create_connection_config(
    username: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    rabbitmq_port: Optional[int] = None,
    keycloak_port: Optional[int] = None,
    keycloak_realm: Optional[str] = None,
    virtual_host: Optional[str] = None,
    is_tls: bool = None,
    env_file: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret_key: Optional[str] = None,
    yaml_file: Optional[str] = None,
) -> ConnectionConfig:
    """
    Create a ConnectionConfig with specified parameters or configuration files.

    Args:
        username (Optional[str]): Username for the connection.
        password (Optional[str]): Password for the connection.
        host (Optional[str]): Host for the connection.
        rabbitmq_port (Optional[int]): RabbitMQ port.
        keycloak_port (Optional[int]): Keycloak port.
        keycloak_realm (Optional[str]): Keycloak realm.
        virtual_host (Optional[str]): Virtual host.
        is_tls (bool): Whether to use TLS. Defaults to True.
        env_file (Optional[str]): Path to the environment file.
        client_id (Optional[str]): Client ID.
        client_secret_key (Optional[str]): Client secret key.
        yaml_file (Optional[str]): Path to the YAML configuration file.

    Returns:
        ConnectionConfig: The created connection configuration.
    """
    if env_file and yaml_file:
        return ConnectionConfig(env_file=env_file, yaml_file=yaml_file)
    if env_file:
        return ConnectionConfig(env_file=env_file)
    return ConnectionConfig(
        username=username,
        password=password,
        host=host,
        rabbitmq_port=rabbitmq_port,
        keycloak_port=keycloak_port,
        keycloak_realm=keycloak_realm,
        virtual_host=virtual_host,
        is_tls=is_tls,
        client_id=client_id,
        client_secret_key=client_secret_key,
    )
