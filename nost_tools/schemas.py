"""
Provides object models for common data structures.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from .simulator import Mode


class InitTaskingParameters(BaseModel):
    """
    Tasking parameters to initialize an execution.
    """

    sim_start_time: datetime = Field(
        ..., description="Earliest possible scenario start time.", alias="simStartTime"
    )
    sim_stop_time: datetime = Field(
        ..., description="Latest possible scenario end time.", alias="simStopTime"
    )
    required_apps: List[str] = Field(
        [], description="List of required applications.", alias="requiredApps"
    )


class InitCommand(BaseModel):
    """
    Command message to initialize an execution.
    """

    tasking_parameters: InitTaskingParameters = Field(
        ...,
        description="Tasking parameters for the initialize command.",
        alias="taskingParameters",
    )


class StartTaskingParameters(BaseModel):
    """
    Tasking parameters to start an execution.
    """

    start_time: Optional[datetime] = Field(
        None,
        description="Wallclock time at which to start execution.",
        alias="startTime",
    )
    sim_start_time: Optional[datetime] = Field(
        None,
        description="Scenario time at which to start execution.",
        alias="simStartTime",
    )
    sim_stop_time: Optional[datetime] = Field(
        None,
        description="Scenario time at which to stop execution.",
        alias="simStopTime",
    )
    time_scaling_factor: float = Field(
        1.0,
        gt=0,
        description="Scenario seconds per wallclock second.",
        alias="timeScalingFactor",
    )


class StartCommand(BaseModel):
    """
    Command message to start an execution.
    """

    tasking_parameters: StartTaskingParameters = Field(
        ...,
        description="Tasking parameters for the start command.",
        alias="taskingParameters",
    )


class StopTaskingParameters(BaseModel):
    """
    Tasking parameters to stop an execution.
    """

    sim_stop_time: datetime = Field(
        ...,
        description="Scenario time at which to stop execution.",
        alias="simStopTime",
    )


class StopCommand(BaseModel):
    """
    Command message to stop an execution.
    """

    tasking_parameters: StopTaskingParameters = Field(
        ...,
        description="Tasking parameters for the stop command.",
        alias="taskingParameters",
    )


class UpdateTaskingParameters(BaseModel):
    """
    Tasking parameters to update an execution.
    """

    time_scaling_factor: float = Field(
        ...,
        gt=0,
        description="Time scaling factor (scenario seconds per wallclock second).",
        alias="timeScalingFactor",
    )
    sim_update_time: datetime = Field(
        ...,
        description="Scenario time at which to update the time scaling factor.",
        alias="simUpdateTime",
    )


class UpdateCommand(BaseModel):
    """
    Command message to update an execution.
    """

    tasking_parameters: UpdateTaskingParameters = Field(
        ...,
        description="Tasking parameters for the stop command.",
        alias="taskingParameters",
    )


class TimeStatusProperties(BaseModel):
    """
    Properties to report time status.
    """

    sim_time: datetime = Field(
        ..., description="Current scenario time.", alias="simTime"
    )
    time: datetime = Field(..., description="Current wallclock time.")


class TimeStatus(BaseModel):
    """
    Message to report time status.
    """

    name: str = Field(
        ..., description="Name of the application providing a time status."
    )
    description: Optional[str] = Field(
        None, description="Description of the application providing a ready status."
    )
    properties: TimeStatusProperties = Field(
        ..., description="Properties for the time status."
    )


class ModeStatusProperties(BaseModel):
    """
    Properties to report mode status.
    """

    mode: Mode = Field(..., description="Current execution mode.")


class ModeStatus(BaseModel):
    """
    Message to report mode status.
    """

    name: str = Field(
        ..., description="Name of the application providing a mode status."
    )
    description: Optional[str] = Field(
        None, description="Description of the application providing a ready status."
    )
    properties: ModeStatusProperties = Field(
        ..., description="Properties for the mode status."
    )


class ReadyStatusProperties(BaseModel):
    """
    Properties to report ready status.
    """

    ready: bool = Field(True, description="True, if this application is ready.")


class ReadyStatus(BaseModel):
    """
    Message to report ready status.
    """

    name: str = Field(
        ..., description="Name of the application providing a ready status."
    )
    description: Optional[str] = Field(
        None, description="Description of the application providing a ready status."
    )
    properties: ReadyStatusProperties = Field(
        ..., description="Properties for the ready status."
    )


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
    tls: bool = Field(False, description="RabbitMQ TLS/SSL.")
    reconnect_delay: int = Field(10, description="Reconnection delay, in seconds.")
    queue_max_size: int = Field(5000, description="Maximum size of the RabbitMQ queue.")
    # BasicProperties
    content_type: str = Field(
        None,
        description="RabbitMQ MIME content type (application/json, text/plain, etc.).",
    )
    content_encoding: str = Field(
        None,
        description="RabbitMQ MIME content encoding (gzip, deflate, etc.).",
    )
    headers: Dict[str, str] = Field(
        None, description="RabbitMQ message headers (key-value pairs)."
    )
    delivery_mode: int = Field(
        None, description="RabbitMQ delivery mode (1: non-persistent, 2: durable)."
    )
    priority: int = Field(None, description="RabbitMQ message priority (0-255).")
    correlation_id: str = Field(
        None, description="RabbitMQ correlation ID for message tracking."
    )
    reply_to: str = Field(
        None, description="RabbitMQ reply-to queue for response messages."
    )
    message_expiration: str = Field(
        None, description="RabbitMQ expiration, in milliseconds."
    )
    message_id: str = Field(None, description="RabbitMQ message ID for tracking.")
    timestamp: datetime = Field(None, description="RabbitMQ message timestamp.")
    type: str = Field(None, description="RabbitMQ message type (e.g., 'text', 'json').")
    user_id: str = Field(None, description="RabbitMQ user ID for authentication.")
    app_id: str = Field(None, description="RabbitMQ application ID for tracking.")
    cluster_id: str = Field(None, description="RabbitMQ cluster ID for tracking.")
    # ConnectionParameters
    host: str = Field("localhost", description="RabbitMQ host.")
    port: int = Field(5672, description="RabbitMQ port.")
    virtual_host: str = Field("/", description="RabbitMQ virtual host.")
    channel_max: int = Field(
        65535, description="RabbitMQ maximum number of channels per connection."
    )
    frame_max: int = Field(131072, description="RabbitMQ maximum frame size in bytes.")
    heartbeat: int = Field(None, description="RabbitMQ heartbeat interval, in seconds.")
    connection_attempts: int = Field(
        1, description="RabbitMQ connection attempts before giving up."
    )
    retry_delay: int = Field(2, description="RabbitMQ retry delay, in seconds.")
    socket_timeout: int = Field(10, description="RabbitMQ socket timeout, in seconds.")
    stack_timeout: int = Field(15, description="RabbitMQ stack timeout, in seconds.")
    locale: str = Field("en_US", description="RabbitMQ locale.")
    blocked_connection_timeout: int = Field(
        None, description="Timeout for blocked connections."
    )


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
    keycloak: Optional[KeycloakConfig] = Field(
        None, description="Keycloak configuration."
    )

    @model_validator(mode="before")
    def validate_keycloak_authentication(cls, values):
        rabbitmq_config = values.get("rabbitmq")
        keycloak_config = values.get("keycloak")

        # Check if rabbitmq_config is a dictionary and validate the keycloak_authentication key
        if (
            isinstance(rabbitmq_config, dict)
            and rabbitmq_config.get("keycloak_authentication", False)
            and not keycloak_config
        ):
            raise ValueError(
                "Keycloak authentication is enabled, but the Keycloak configuration is missing."
            )
        return values


class WallclockOffsetProperties(BaseModel):
    """
    Properties to report wallclock offset.
    """

    wallclock_offset_refresh_interval: Optional[int] = Field(
        10800, description="Wallclock offset refresh interval, in seconds."
    )
    ntp_host: Optional[str] = Field(
        "pool.ntp.org", description="NTP host for wallclock offset synchronization."
    )


class GeneralConfig(BaseModel):
    prefix: Optional[str] = Field("nost", description="Execution prefix.")


class TimeScaleUpdateSchema(BaseModel):
    """
    Provides a scheduled update to the simulation time scale factor.
    """

    time_scale_factor: float = Field(
        ..., description="Scenario seconds per wallclock second"
    )
    sim_update_time: datetime = Field(
        ..., description="Scenario time that the update will occur"
    )


class LoggingConfig(BaseModel):
    """
    Configuration for logging.
    """

    enable_file_logging: Optional[bool] = Field(
        False, description="Enable file logging."
    )
    log_dir: Optional[str] = Field(
        "logs", description="Directory path for log files."
    )
    log_filename: Optional[str] = Field(None, description="Path to the log file.")
    log_level: Optional[str] = Field(
        "INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
    )
    max_bytes: Optional[int] = Field(
        10 * 1024 * 1024,
        description="Maximum size of the log file in bytes. Default is 10MB.",
    )
    backup_count: Optional[int] = Field(
        5, description="Number of backup log files to keep."
    )
    log_format: Optional[str] = Field(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="Format of the log messages.",
    )


class ManagerConfig(LoggingConfig):
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
    time_scale_updates: List[TimeScaleUpdateSchema] = Field(
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
    is_scenario_time_step: bool = Field(
        True,
        description="If True, time_step is in scenario time and won't be scaled. If False, time_step is in wallclock time and will be scaled by the time scale factor.",
    )
    is_scenario_time_status_step: bool = Field(
        True,
        description="If True, time_status_step is in scenario time and won't be scaled. If False, time_status_step is in wallclock time and will be scaled by the time scale factor.",
    )

    @model_validator(mode="before")
    def scale_time(cls, values):
        time_scale_factor = values.get("time_scale_factor", 1.0)

        if "time_step" in values and not values.get("is_scenario_time_step", True):
            time_step = values["time_step"]
            if isinstance(time_step, str):
                hours, minutes, seconds = map(int, time_step.split(":"))
                time_step = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            if isinstance(time_step, timedelta):
                values["time_step"] = timedelta(
                    seconds=time_step.total_seconds() * time_scale_factor
                )

        if "time_status_step" in values and not values.get(
            "is_scenario_time_status_step", True
        ):
            time_status_step = values["time_status_step"]
            if isinstance(time_status_step, str):
                hours, minutes, seconds = map(int, time_status_step.split(":"))
                time_status_step = timedelta(
                    hours=hours, minutes=minutes, seconds=seconds
                )
            if isinstance(time_status_step, timedelta):
                values["time_status_step"] = timedelta(
                    seconds=time_status_step.total_seconds() * time_scale_factor
                )

        return values


class ManagedApplicationConfig(LoggingConfig):
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
    is_scenario_time_step: bool = Field(
        True,
        description="If True, time_step is in scenario time and won't be scaled. If False, time_step is in wallclock time and will be scaled by the time scale factor.",
    )
    is_scenario_time_status_step: bool = Field(
        True,
        description="If True, time_status_step is in scenario time and won't be scaled. If False, time_status_step is in wallclock time and will be scaled by the time scale factor.",
    )

    @model_validator(mode="before")
    def scale_time(cls, values):
        time_scale_factor = values.get("time_scale_factor", 1.0)

        if "time_step" in values and not values.get("is_scenario_time_step", True):
            time_step = values["time_step"]
            if isinstance(time_step, str):
                hours, minutes, seconds = map(int, time_step.split(":"))
                time_step = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            if isinstance(time_step, timedelta):
                values["time_step"] = timedelta(
                    seconds=time_step.total_seconds() * time_scale_factor
                )

        if "time_status_step" in values and not values.get(
            "is_scenario_time_status_step", True
        ):
            time_status_step = values["time_status_step"]
            if isinstance(time_status_step, str):
                hours, minutes, seconds = map(int, time_status_step.split(":"))
                time_status_step = timedelta(
                    hours=hours, minutes=minutes, seconds=seconds
                )
            if isinstance(time_status_step, timedelta):
                values["time_status_step"] = timedelta(
                    seconds=time_status_step.total_seconds() * time_scale_factor
                )

        return values


class LoggerApplicationConfig(BaseModel):
    set_offset: Optional[bool] = Field(True, description="Set offset.")
    time_scale_factor: Optional[float] = Field(1.0, description="Time scale factor.")
    time_step: Optional[timedelta] = Field(
        timedelta(seconds=1), description="Time step for swe_change."
    )
    time_status_step: Optional[timedelta] = Field(
        timedelta(seconds=10), description="Time status step."
    )
    time_status_init: Optional[datetime] = Field(
        datetime.now(), description="Time status init."
    )
    shut_down_when_terminated: Optional[bool] = Field(
        False, description="Shut down when terminated."
    )
    manager_app_name: Optional[str] = Field(
        "manager", description="Manager application name."
    )


class ApplicationConfig(BaseModel):
    set_offset: Optional[bool] = Field(True, description="Set offset.")
    time_scale_factor: Optional[float] = Field(1.0, description="Time scale factor.")
    time_step: Optional[timedelta] = Field(
        timedelta(seconds=1), description="Time step for swe_change."
    )
    time_status_step: Optional[timedelta] = Field(
        timedelta(seconds=10), description="Time status step."
    )
    time_status_init: Optional[datetime] = Field(
        datetime.now(), description="Time status init."
    )
    shut_down_when_terminated: Optional[bool] = Field(
        False, description="Shut down when terminated."
    )
    manager_app_name: Optional[str] = Field(
        "manager", description="Manager application name."
    )


class ExecConfig(BaseModel):
    general: Optional[GeneralConfig] = Field(
        None, description="General configuration for the execution."
    )
    manager: Optional[ManagerConfig] = Field(None, description="Manager configuration.")
    managed_applications: Optional[Dict[str, ManagedApplicationConfig]] = Field(
        default_factory=lambda: {"default": ManagedApplicationConfig()},
        description="Dictionary of managed application configurations, keyed by application name.",
    )
    logger_application: Optional[LoggerApplicationConfig] = Field(
        None, description="Logger application configuration."
    )
    application: Optional[ApplicationConfig] = Field(
        None, description="Application configuration."
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
    username: Optional[str] = Field("admin", description="Username for authentication.")
    password: Optional[str] = Field("admin", description="Password for authentication.")
    client_id: Optional[str] = Field(None, description="Client ID for authentication.")
    client_secret_key: Optional[str] = Field(
        None, description="Client secret key for authentication."
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
    wallclock_offset_properties: WallclockOffsetProperties = Field(
        ..., description="Properties for wallclock offset."
    )
    credentials: Credentials = Field(..., description="Credentials for authentication.")
    server_configuration: Config = (
        Field(..., description="Simulation configuration."),
    )
    simulation_configuration: SimulationConfig = Field(
        ..., description="Simulation configuration."
    )
    application_configuration: Optional[Dict] = Field(
        None, description="Application-specific, user-provided configuration."
    )
    yaml_file: Optional[str] = Field(
        None, description="Path to the YAML file containing the configuration."
    )
