.. _yamlConfig:

YAML
====

The NOS-T Tools library requires a Yet Another Markup Language (YAML) configuration file. This file adopts a format similar to `AsyncAPI <https://www.asyncapi.com/>`__ to define the connection configuration for the RabbitMQ broker and Keycloak authentication servers.

Configuration Overview
----------------------

The YAML files is composed of the following sections:

1. Info: Contains metadata about the YAML configuration file.
2. Servers: Contains the connection configuration for the RabbitMQ broker and Keycloak authentication servers.
3. Execution: Contains the execution configuration for the NOS-T Tools library.
4. Channels: Contains the channel configuration for the NOS-T Tools library.

Each section is explained in detail below.

Info Section
^^^^^^^^^^^^
Contains metadata about the configuration file. This does not influence the operation of the NOS-T Tools library, it is merely for documentation and informational purposes.

.. autopydantic_model:: nost_tools.schemas.InfoConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    info:
..      title: Novel Observing Strategies Testbed (NOS-T) YAML Configuration
..      version: '1.0.0'
..      description: Version-controlled configuration file for Snow Observing Systems (SOS) project

.. literalinclude:: example.yml
	:lines: 1-4

Servers Section
^^^^^^^^^^^^^^^

Defines connection parameters for the RabbitMQ message broker and Keycloak authentication server.

RabbitMQ Configuration
""""""""""""""""""""""

.. autopydantic_model:: nost_tools.schemas.RabbitMQConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    servers:
..      rabbitmq:
..        keycloak_authentication: False  # Enable/disable Keycloak authentication
..        host: "localhost"               # RabbitMQ server hostname
..        port: 5672                      # RabbitMQ server port (5672 for non-TLS, 5671 for TLS)
..        tls: False                      # Enable/disable TLS encryption
..        virtual_host: "/"               # RabbitMQ virtual host
..        message_expiration: "60000"     # Message expiration time in milliseconds
..        delivery_mode: 2                # Message delivery mode (1=transient, 2=durable)
..        content_type: "text/plain"      # Default content type for messages
..        heartbeat: 600                  # Connection heartbeat interval in seconds
..        connection_attempts: 3          # Number of connection retry attempts
..        retry_delay: 5                  # Delay between retry attempts in seconds
..        reconnect_delay: 10             # Delay before reconnection attempt in seconds
..        blocked_connection_timeout: 300 # Timeout for blocked connections in seconds
..        queue_max_size: 1000            # Max messages queued during connection drop
..        frame_max: 131072              # Maximum AMQP frame size in bytes
..        socket_timeout: 10.0            # Socket timeout in seconds
..        stack_timeout: 15.0             # Stack timeout in seconds

.. literalinclude:: example.yml
	:lines: 5-23

Keycloak Configuration
""""""""""""""""""""""

.. autopydantic_model:: nost_tools.schemas.KeycloakConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    servers:
..      keycloak:
..        host: "nost.smce.nasa.gov"      # Keycloak server hostname
..        port: 8443                      # Keycloak server port
..        tls: True                       # Enable/disable TLS encryption
..        token_refresh_interval: 240     # Token refresh interval in seconds
..        realm: "NOS-T"                  # Keycloak realm name

.. literalinclude:: example.yml
	:lines: 24-29

Execution Section
^^^^^^^^^^^^^^^^^

Defines parameters controlling simulation execution and time management.

General Configuration
"""""""""""""""""""""

.. autopydantic_model:: nost_tools.schemas.GeneralConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    execution:
..      general:
..        prefix: sos                                # Prefix for channel addresses
..        wallclock_offset_refresh_interval: 10800   # Wallclock offset refresh interval in seconds
..        ntp_host: "pool.ntp.org"                   # NTP host for time synchronization
..        resume_tolerance: "12:00:00"               # Default tolerance for resume requests (HH:MM:SS)

.. literalinclude:: example.yml
	:lines: 30-35

Application Configuration
"""""""""""""""""""""""""

Configures unmanaged applications (those that do not receive commands from a Manager). Each application is identified by name under the ``execution.applications`` dictionary. Application-specific parameters can be defined under ``configuration_parameters``.

.. autopydantic_model:: nost_tools.schemas.ApplicationConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    execution:
..      applications:
..        dashboard:
..          set_offset: False
..          shut_down_when_terminated: True
..          configuration_parameters:
..            refresh_rate: 5

.. literalinclude:: example.yml
	:lines: 36-44

Manager Configuration
"""""""""""""""""""""

.. autopydantic_model:: nost_tools.schemas.ManagerConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    execution:
..      manager:
..        sim_start_time: "2019-03-01T23:59:59+00:00"  # Simulation start time (ISO 8601)
..        sim_stop_time: "2019-03-10T23:59:59+00:00"   # Simulation end time (ISO 8601)
..        start_time:                                  # Optional real-world start time (ISO 8601)
..        time_step: "0:00:01"                         # Simulation time increment per step
..        time_scale_factor: 288                       # Acceleration factor for simulation time
..        time_status_step: "0:00:01"                  # Interval for publishing time status messages
..        is_scenario_time_status_step: False           # Whether time_status_step is in scenario time
..        time_status_init: "2019-03-01T23:59:59+00:00" # Initial time for status messages (ISO 8601)
..        command_lead: "0:00:05"                      # Lead time for commands
..        required_apps:                               # List of required applications
..          - manager
..          - planner
..          - appender
..          - simulator
..        init_retry_delay_s: 5                        # Initialization retry delay in seconds
..        init_max_retry: 5                            # Maximum initialization retry attempts
..        set_offset: True                             # Enable/disable time offset calculation
..        shut_down_when_terminated: False             # Automatically shut down when simulation ends

.. literalinclude:: example.yml
	:lines: 45-68

Managed Application Configuration
"""""""""""""""""""""""""""""""""

Each managed application is identified by name under the ``execution.managed_applications`` dictionary. If a field is not provided, default values are used. Application-specific parameters can be defined under ``configuration_parameters``.

.. autopydantic_model:: nost_tools.schemas.ManagedApplicationConfig
  :members:
  :inherited-members: BaseModel

Example:

.. .. code-block:: yaml

..    execution:
..      managed_applications:
..        planner:
..          time_scale_factor: 288                       # Application time scale factor
..          time_step: "0:00:01"                         # Application time step
..          is_scenario_time_step: False                  # Whether time_step is in scenario time
..          set_offset: True                             # Enable/disable time offset calculation
..          time_status_step: "0:00:10"                  # Interval for publishing time status
..          is_scenario_time_status_step: False           # Whether time_status_step is in scenario time
..          shut_down_when_terminated: False             # Auto shutdown when complete
..          manager_app_name: "manager"                  # Name of the manager application
..          configuration_parameters:                    # Application-specific parameters
..            planning_horizon: 3600

.. literalinclude:: example.yml
	:lines: 69-94

Logging Configuration
"""""""""""""""""""""

File logging can be enabled per-application through the YAML configuration. Logging parameters are inherited by ``ManagerConfig``, ``ManagedApplicationConfig``, and ``ApplicationConfig``. When ``enable_file_logging`` is set to ``True``, the ``configure_file_logging()`` method is automatically called during ``start_up()``.

.. autopydantic_model:: nost_tools.schemas.LoggingConfig
  :members:
  :inherited-members: BaseModel

Unmanaged application logging example:

.. literalinclude:: example.yml
	:lines: 36-37, 40-42

Manager logging example:

.. literalinclude:: example.yml
	:lines: 45, 64-68

Managed application logging example:

.. literalinclude:: example.yml
	:lines: 69-70, 79-83

Channels Section
^^^^^^^^^^^^^^^^
Defines the messaging channels used for communication between components. This entire section is optional. If a user wants to define each channel and queue for organizational purposes, they can do so here. Otherwise, the NOS-T Tools library will create default channels and queues.

Channels follow this structure:

.. code-block:: yaml

   channels:
     <component>:
       <message_type>:
         address: '<prefix>.<component>.<message_type>'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: <prefix>
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0

Example:

.. literalinclude:: example.yml
	:lines: 95-

In this example YAML file, the configuration includes predefined channels for:

1. Satellite components (location, status.mode, status.ready, status.time)
2. Manager components (init, start, stop, status.mode, status.time)

Each channel specifies:

* An address pattern used as the routing key
* AMQP binding configuration including exchange properties

Using the Configuration File
----------------------------

Applications using the NOS-T Tools library specify the path to the YAML configuration file when initializing. The library reads this file to establish connections to the RabbitMQ broker and Keycloak authentication server and to configure the execution parameters. Refer to :ref:`nost_publisher_consumer_example` for an example of how the configuration file is used within the NOS-T Tools library.

Complete Configuration Example
------------------------------

Below is a complete example of a YAML configuration file that can be used with NOS-T Tools:

.. literalinclude:: example.yml
