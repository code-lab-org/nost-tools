YAML
====

The NOS-T Tools library requires a Yet Another Markup Language (YAML) configuration file. This file adopts a format similar to `AsyncAPI <https://www.asyncapi.com/>`__ to define the connection configuration for the RabbitMQ broker and Keycloak authentication servers.


Overview of Configuration Sections
----------------------------------

1. Info: Contains metadata about the YAML configuration file.
2. Servers: Contains the connection configuration for the RabbitMQ broker and Keycloak authentication servers.
3. Execution: Contains the execution configuration for the NOS-T Tools library.
4. Channels: Contains the channel configuration for the NOS-T Tools library.

Configuration Details
--------------------

Info Section
^^^^^^^^^^^
Contains metadata about the configuration file. This does not influence the operation of the NOS-T Tools library, it is merely for documentation and informational purposes.

Example:

.. code-block:: yaml

   info:
     title: Novel Observing Strategies Testbed (NOS-T) YAML Configuration
     version: '1.0.0'
     description: Version-controlled configuration file for Snow Observing Systems (SOS) project

Parameters:

* **title**: The name of the configuration
* **version**: Version number of the configuration file
* **description**: Brief description of the configuration file's purpose

Servers Section
^^^^^^^^^^^^^
Defines connection parameters for the RabbitMQ message broker and Keycloak authentication server.

RabbitMQ Configuration
"""""""""""""""""""""

.. code-block:: yaml

   servers:
     rabbitmq:
       keycloak_authentication: False  # Enable/disable Keycloak authentication
       host: "localhost"               # RabbitMQ server hostname
       port: 5672                      # RabbitMQ server port (5672 for non-TLS, 5671 for TLS)
       tls: False                      # Enable/disable TLS encryption
       virtual_host: "/"               # RabbitMQ virtual host
       message_expiration: "60000"     # Message expiration time in milliseconds
       delivery_mode: 2                # Message delivery mode (1=transient, 2=durable)
       content_type: "text/plain"      # Default content type for messages
       heartbeat: 30                   # Connection heartbeat interval in seconds
       connection_attempts: 3          # Number of connection retry attempts
       retry_delay: 5                  # Delay between retry attempts in seconds

Keycloak Configuration
""""""""""""""""""""

.. code-block:: yaml

   servers:
     keycloak:
       host: "nost.smce.nasa.gov"      # Keycloak server hostname
       port: 8443                      # Keycloak server port
       tls: True                       # Enable/disable TLS encryption
       token_refresh_interval: 10      # Token refresh interval in seconds
       realm: "NOS-T"                  # Keycloak realm name

Execution Section
^^^^^^^^^^^^^^^
Defines parameters controlling simulation execution and time management.

General Configuration
"""""""""""""""""""

.. code-block:: yaml

   execution:
     general:
       prefix: sos                     # Prefix for channel addresses

Manager Configuration
""""""""""""""""""

Parameters for the simulation manager component:

.. code-block:: yaml

   execution:
     manager:
       sim_start_time: "2019-03-01T23:59:59+00:00"  # Simulation start time (ISO 8601)
       sim_stop_time: "2019-03-10T23:59:59+00:00"   # Simulation end time (ISO 8601)
       start_time:                                  # Optional real-world start time (ISO 8601)
       time_step: "0:00:01"                         # Simulation time increment per step
       time_scale_factor: 288                       # Acceleration factor for simulation time
       time_scale_updates: []                       # List of time scale changes during simulation
       time_status_step: "0:00:01"                  # Interval for publishing time status messages
       time_status_init: "2019-03-01T23:59:59+00:00" # Initial time for status messages (ISO 8601)
       command_lead: "0:00:05"                      # Lead time for commands
       required_apps:                               # List of required applications
         - manager
         - planner
         - appender
         - simulator
       init_retry_delay_s: 5                        # Initialization retry delay in seconds
       init_max_retry: 5                            # Maximum initialization retry attempts
       set_offset: True                             # Enable/disable time offset calculation
       shut_down_when_terminated: False             # Automatically shut down when simulation ends

Managed Application Configuration
"""""""""""""""""""""""""""""

Configuration for applications controlled by the manager:

.. code-block:: yaml

   execution:
     managed_application:
       time_scale_factor: 288                       # Application time scale factor
       time_step: "0:00:01"                         # Application time step
       set_offset: True                             # Enable/disable time offset calculation 
       time_status_step: "0:00:10"                  # Interval for publishing time status
       time_status_init: "2019-03-01T00:00:00+00:00" # Initial time for status messages
       shut_down_when_terminated: False             # Auto shutdown when complete
       manager_app_name: "manager"                  # Name of the manager application

Channels Section
^^^^^^^^^^^^^^
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

In this example YAML file, the configuration includes predefined channels for:

1. Satellite components (location, status.mode, status.ready, status.time)
2. Manager components (init, start, stop, status.mode, status.time)

Each channel specifies:

* An address pattern used as the routing key
* AMQP binding configuration including exchange properties

Using the Configuration File
---------------------------

Applications using the NOS-T Tools library specify the path to the YAML configuration file when initializing. The library reads this file to establish connections to the RabbitMQ broker and Keycloak authentication server and to configure the execution parameters.

Complete Configuration Example
-----------------------------

Below is a complete example of a YAML configuration file that can be used with NOS-T Tools:

.. code-block:: yaml

   info:
     title: Novel Observing Strategies Testbed (NOS-T) YAML Configuration
     version: '1.0.0'
     description: Version-controlled AsyncAPI document for RabbitMQ event broker with Keycloak authentication within NOS-T
   servers:
     rabbitmq:
       # Production configuration
       # keycloak_authentication: True
       # host: "nost.smce.nasa.gov"
       # port: 5671
       # tls: True
       # virtual_host: "/"

       # Local development configuration
       keycloak_authentication: False
       host: "localhost"
       port: 5672
       tls: False
       virtual_host: "/"

       # Common settings
       message_expiration: "60000"     # in milliseconds, message expiration time
       delivery_mode: 2                # 1=transient, 2=durable
       content_type: "text/plain"
       heartbeat: 30                   # in seconds
       connection_attempts: 3
       retry_delay: 5                  # in seconds
     
     keycloak:
       host: "nost.smce.nasa.gov"
       port: 8443
       tls: True
       token_refresh_interval: 10      # in seconds
       realm: "NOS-T"
   
   execution:
     general:
       prefix: sos                     # Prefix for channel addresses
     
     manager:
       sim_start_time: "2019-03-01T23:59:59+00:00"
       sim_stop_time: "2019-03-10T23:59:59+00:00"
       start_time:
       time_step: "0:00:01"
       time_scale_factor: 288
       time_scale_updates: []
       time_status_step: "0:00:01"     # 1 second * time scale factor
       time_status_init: "2019-03-01T23:59:59+00:00"
       command_lead: "0:00:05"
       required_apps:
         - manager
         - planner
         - appender
         - simulator
       init_retry_delay_s: 5
       init_max_retry: 5
       set_offset: True
       shut_down_when_terminated: False
     
     managed_application:
       time_scale_factor: 288
       time_step: "0:00:01"            # 1 second * time scale factor 
       set_offset: True
       time_status_step: "0:00:10"     # 10 seconds * time scale factor
       time_status_init: "2019-03-01T00:00:00+00:00"
       shut_down_when_terminated: False
       manager_app_name: "manager"
   
   channels:
     satellite: 
       location:
         address: 'sos.constellation.location'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       status.mode:
         address: 'sos.constellation.status.mode'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       status.ready:
         address: 'sos.constellation.status.ready'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       status.time:
         address: 'sos.constellation.status.time'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
     
     manager:
       init:
         address: 'sos.manager.init'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       start:
         address: 'sos.manager.start'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       stop:
         address: 'sos.manager.stop'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       status.mode:
         address: 'sos.manager.status.mode'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0
       
       status.time:
         address: 'sos.manager.status.time'
         bindings:
           amqp:
             is: routingKey
             exchange:
               name: sos
               type: topic
               durable: false
               autoDelete: true
               vhost: /
             bindingVersion: 0.3.0