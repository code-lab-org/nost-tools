"""
Configuration Settings.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yaml
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field, ValidationError, model_validator

logger = logging.getLogger(__name__)


class InfoConfig(BaseModel):
    title: Optional[str] = Field(None, description="Title of the simulation.")
    version: Optional[str] = Field(None, description="Version of the simulation.")
    description: Optional[str] = Field(
        None, description="Description of the simulation."
    )


class RabbitMQConfig(BaseModel):
    keycloak_authentication: bool = Field(
        False, description="Keycloak authentication for RabbitMQ."
    )
    host: str = Field("localhost", description="RabbitMQ host.")
    port: int = Field(5672, description="RabbitMQ port.")
    tls: bool = Field(False, description="RabbitMQ TLS/SSL.")
    virtual_host: str = Field("/", description="RabbitMQ virtual host.")
    message_expiration: str = Field(
        "60000", description="RabbitMQ expiration, in milliseconds."
    )
    delivery_mode: int = Field(
        2, description="RabbitMQ delivery mode (1: non-persistent, 2: durable)."
    )
    content_type: str = Field(
        "text/plain",
        description="RabbitMQ MIME content type (application/json, text/plain, etc.).",
    )
    heartbeat: int = Field(30, description="RabbitMQ heartbeat interval, in seconds.")
    connection_attempts: int = Field(
        3, description="RabbitMQ connection attempts before giving up."
    )
    retry_delay: int = Field(5, description="RabbitMQ retry delay, in seconds.")


class KeycloakConfig(BaseModel):
    host: str = Field("localhost", description="Keycloak host.")
    port: int = Field(8080, description="Keycloak port.")
    realm: str = Field("master", description="Keycloak realm.")
    tls: bool = Field(False, description="Keycloak TLS/SSL.")
    token_refresh_interval: int = Field(
        60, description="Keycloak token refresh interval, in seconds."
    )


class ServersConfig(BaseModel):
    rabbitmq: RabbitMQConfig = Field(..., description="RabbitMQ configuration.")
    keycloak: KeycloakConfig = Field(..., description="Keycloak configuration.")


class GeneralConfig(BaseModel):
    prefix: str = Field("nost", description="Execution prefix.")


class ManagerConfig(BaseModel):
    sim_start_time: Optional[datetime] = Field(
        None, description="Simulation start time."
    )
    sim_stop_time: Optional[datetime] = Field(None, description="Simulation stop time.")
    start_time: Optional[datetime] = Field(None, description="Execution start time.")
    time_step: timedelta = Field(
        timedelta(seconds=1),
        description="Time step for the simulation.",
    )
    time_scale_factor: float = Field(1.0, description="Time scale factor.")
    time_scale_updates: List[str] = Field(
        default_factory=list, description="List of time scale updates."
    )
    time_status_step: Optional[timedelta] = Field(None, description="Time status step.")
    time_status_init: Optional[datetime] = Field(None, description="Time status init.")
    command_lead: timedelta = Field(
        timedelta(seconds=0), description="Command lead time."
    )
    required_apps: List[str] = Field(
        default_factory=list, description="List of required applications."
    )
    init_retry_delay_s: int = Field(5, description="Initial retry delay in seconds.")
    init_max_retry: int = Field(5, description="Initial maximum retry attempts.")
    set_offset: bool = Field(True, description="Set offset.")
    shut_down_when_terminated: bool = Field(
        False, description="Shut down when terminated."
    )

    @model_validator(mode="before")
    def scale_time(cls, values):
        time_scale_factor = values.get("time_scale_factor", 1.0)

        if "time_status_step" in values:
            time_status_step = values["time_status_step"]
            if isinstance(time_status_step, str):
                time_status_step = timedelta(
                    seconds=float(time_status_step.split(":")[-1])
                )
            if isinstance(time_status_step, timedelta):
                values["time_status_step"] = timedelta(
                    seconds=time_status_step.total_seconds() * time_scale_factor
                )

        return values


class ManagedApplicationConfig(BaseModel):
    time_scale_factor: float = Field(1.0, description="Time scale factor.")
    time_step: timedelta = Field(
        timedelta(seconds=1), description="Time step for swe_change."
    )
    set_offset: bool = Field(True, description="Set offset.")
    time_status_step: timedelta = Field(None, description="Time status step.")
    time_status_init: datetime = Field(None, description="Time status init.")
    shut_down_when_terminated: bool = Field(
        False, description="Shut down when terminated."
    )
    manager_app_name: str = Field("manager", description="Manager application name.")

    @model_validator(mode="before")
    def scale_time(cls, values):
        time_scale_factor = values.get("time_scale_factor", 1.0)

        if "time_step" in values:
            time_step = values["time_step"]
            if isinstance(time_step, str):
                time_step = timedelta(seconds=float(time_step.split(":")[-1]))
            if isinstance(time_step, timedelta):
                values["time_step"] = timedelta(
                    seconds=time_step.total_seconds() * time_scale_factor
                )

        if "time_status_step" in values:
            time_status_step = values["time_status_step"]
            if isinstance(time_status_step, str):
                time_status_step = timedelta(
                    seconds=float(time_status_step.split(":")[-1])
                )
            if isinstance(time_status_step, timedelta):
                values["time_status_step"] = timedelta(
                    seconds=time_status_step.total_seconds() * time_scale_factor
                )

        return values


class ExecConfig(BaseModel):
    general: GeneralConfig
    manager: ManagerConfig
    managed_application: ManagedApplicationConfig


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
    client_id: Optional[str] = Field("", description="Client ID for authentication.")
    client_secret_key: Optional[str] = Field(
        "", description="Client secret key for authentication."
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
        yaml_file (str): Path to the YAML configuration file
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        rabbitmq_host: str = None,
        rabbitmq_port: int = None,
        keycloak_host: str = None,
        keycloak_port: int = None,
        keycloak_realm: str = None,
        client_id: str = None,
        client_secret_key: str = None,
        virtual_host: str = None,
        is_tls: bool = True,
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
            yaml_file (str): Path to the YAML configuration file
        """
        self.username = username
        self.password = password
        self.rabbitmq_host = rabbitmq_host
        self.keycloak_host = keycloak_host
        self.rabbitmq_port = rabbitmq_port
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
        if self.server_config.servers.rabbitmq.keycloak_authentication:
            required_fields = [
                "USERNAME",
                "PASSWORD",
                "CLIENT_ID",
                "CLIENT_SECRET_KEY",
            ]
        else:
            required_fields = ["USERNAME", "PASSWORD"]

        env_data = {field: os.getenv(field) for field in required_fields}

        missing_fields = [field for field, value in env_data.items() if value is None]
        if missing_fields:
            raise EnvironmentVariableError(
                f"Missing required fields in .env file: {', '.join(missing_fields)}"
            )

        try:
            if self.server_config.servers.rabbitmq.keycloak_authentication:
                self.credentials_config = Credentials(
                    username=env_data["USERNAME"],
                    password=env_data["PASSWORD"],
                    client_id=env_data["CLIENT_ID"],
                    client_secret_key=env_data["CLIENT_SECRET_KEY"],
                )
            else:
                self.credentials_config = Credentials(
                    username=env_data["USERNAME"],
                    password=env_data["PASSWORD"],
                )
        except ValidationError as err:
            raise EnvironmentVariableError(f"Invalid environment variables: {err}")

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
            except AssertionError as e:
                raise ValueError(f"Assertion error: {e}")
        else:
            try:
                self.yaml_config = Config(
                    servers=ServersConfig(
                        rabbitmq=RabbitMQConfig(
                            host=self.rabbitmq_host,
                            port=self.rabbitmq_port,
                            virtual_host=self.virtual_host,
                            tls=self.is_tls,
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

        if (
            self.username is not None
            and self.password is not None
            and self.client_id is not None
            and self.client_secret_key is not None
        ):
            logger.info("Using provided credentials.")
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
        )
