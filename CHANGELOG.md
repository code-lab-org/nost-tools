# NOS-T Change Log

## 2.0.0
Added:
- Integrated Keycloak for robust identity and access management (IAM) of AWS SMCE resources.
- Implemented secure authentication and authorization mechanisms.
- Consolidated execution configuration into a single YAML file.
- Comprehensive updates to the documentation.
- Detailed instructions for configuring and using the new messaging protocol, IAM integration, and unified execution configuration.

Changed:
- Replaced Paho-MQTT library with Pika-AMQP for better performance and reliability.
- Updated all relevant modules and configurations to support the new messaging protocol.

## 2.0.1
Added:
- Added `socket_timeout`, `stack_timeout`, and `locale` fields of `pika.connection.ConnectionParameters` to YAML (66-update-ssltls-configuration)

Changed:
- Made `manager`, `managed_application`, and `logger_application` YAML fields optional (64-make-logger_application-field-optional-in-execution-section-of-pydantic-class)
- Updated defaults values for `pika.connection.ConnectionParameters` and `pika.spec.BasicProperties` to mirror those of Pika if not set in YAML file (66-update-ssltls-configuration)
- Updated SSL configuration to use `ssl.create_default_context()` (66-update-ssltls-configuration)

## 2.0.2
Added:
- Added optional `reconnect_delay` YAML field in the `servers`.`rabbitmq` section, with default value of 10 seconds.
- Used `model_validator` to check `servers.rabbitmq.keycloak_authentication`. If `servers.rabbitmq.keycloak_authentication` is `True` and `servers.keycloak` is `None`, raise a `ValueError`.

Changed:
- Updated `on_close_callback` of `pika.SelectConnection` to react to connection failure events. The callback attempts to recover the connection.
- Made `servers.keycloak` YAML field optional. When running NOS-T Tools on localhost, `servers.keycloak` is not necessary, so it is now optional.
- Fixed scaling of `time_status_step` in `ManagerConfig`, and `time_step` and `time_status_step` in `ManagedApplicationConfig`. The code now correctly parses hours, minutes, and seconds from the string format "HH:MM:SS" and calculates the total seconds accordingly. Total seconds are then correctly scaled by the `time_scale_factor`.

## 2.0.3
Added: 
- GitHub Action for PyPi publishing

Changed:
- Updated PyDantic model to allow for multiple managed applications to be configured using a dictionary for `execution.managed_applications.<app name>`. If a field is not provided, default values specified in `ManagedApplicationConfig` are used for all applications.
- Updated the `start_up()` method to filter the necessary fields within the dictionary. Ensure that only the execution parameters for the specific application (e.g., "planner") are pulled and applied for each application separately.

## 2.0.4
Added:

Changed:
- Refactored `manager.py` so that `execute_test_plan` always runs in a background thread.

## 2.0.5
Added:
- Implemented a heartbeat-safe sleep mechanism called `_sleep_with_heartbeat()` in the Manager class

Changed:
- Modified `_execute_test_plan_impl()` to use the new heartbeat-safe sleep method for all long-duration sleeps in the Manager class
- Update authors, version, and release date in `CITATION.cff`

## 2.1.0
Added:
- Added `frame_max` and `blocked_connection_timeout` to YAML for use in `pika.connection.ConnectionParameters` within Application class
- Added `content_type`, `content_encoding`, `headers`, `priority`, `correlation_id`, `reply_to`, `message_expiration`, `message_id`, `timestamp`, `type`, `user_id`, `app_id`, and `cluster_id` to YAML for use in `pika.spec.BasicProperties` within Application class
- Refresh Keycloak access token before attempting reconnection in `reconnect()` method, as the token may have expired during connection drop
- Added `servers.rabbitmq.queue_max_size` to YAML, establishing the maximum number of messages that can be queued in `self._message_queue` during connection drop
- Introduced a new private method `_setup_signal_handlers()` in the `Application` class to handle system signals (SIGINT and SIGTERM), ensuing the application can shut down gracefully when interrupted (e.g., via CTRL+C or termination signals)
- Introduced a new private method `_cleanup_resources()` that cleans up resources used by joblib and Python's multiprocessing module during execution of `shut_down()`
- New callback observer classes for flexible event handling:
  - `PropertyChangeCallback`: Triggers a custom callback function when a specific property changes
  - `ScenarioTimeIntervalCallback`: Executes a callback at fixed intervals in simulation time
  - `WallclockTimeIntervalCallback`: Executes a callback at fixed intervals in real-world time, independent of simulation speed

Changed:
- Modified `delete_all_queues_and_exchanges()` method to check if connection is open before attempting to clean up
- Modified `on_connection_closed()` method attempt to clean up
- Modified `tick()` method to only perform time calculation if the entity has been initizlied
- Removed exchange and queue declaration by `yamless_declare_bind_queue()` in `send_message()` method
- Modified `on_channel_closed` and `on_connection_closed` methods to delete queues only when the connection or channel is intentionally closed. If the connection drops unexpectedly due to network issues, queues are retained. This ensures that the connection can be re-established without needing to redeclare and rebind queues.
- Queues are now declared with `auto_delete=False` and `durable=True`. This configuration ensures that queues are not deleted during unexpected network issues, but only when intentionally closed, such as at the end of a simulation.
- Exchanges are now declared with `auto_delete=True` and `durable=True`. This configuration ensures that exchanges are deleted only when no more queues are bound to it, such as the end of a simulation run.
- Messages that fail to send due to a connection drop are added to the `self._message_queue` dictionary in the `send_message` method. After reconnection by the `reconnect` method, these queued messages are later dispatched asynchronously via the `_process_message_queue` method, which is scheduled using `self.connection.ioloop.call_later`.
- Updated SSL context for TLS configuration to that of Amazon MQ for RabbitMQ in `start_up` method
- Updated `add_message_callback` method to create a `_saved_callbacks` list to store all registered callbacks. Each entry is a tuple of `(app_name, app_topic, user_callback)` 
- Updated `on_channel_open`  to check for and restore saved callbacks in `_saved_callbacks`, each saved callback is re-registered by calling the `add_message_callback` method
- Updated `reconnect` to reset `_callbacks_per_topic` dictionary to prevent duplicate callbacks when restoring after reconnection 

## 2.1.1 
Added:
- Introduces a new boolean flags to explicitly define the time domain for time_step and time_status_step. These flags will determine whether the associated values are interpreted in ST (unscaled) or WCT (scaled by the time scale factor).

## 2.2.0
Added:
- Introduced `TimeScaleUpdateSchema` in schemas.py, which allows users to define time scale updates in the YAML configuration file at `execution.manager.time_scale_updates`, each update can be defined by `time_scale_factor` and `sim_update_time`. For example:
  ```yaml
  time_scale_updates:
    - time_scale_factor: 120.0
      sim_update_time: "2020-01-01T08:20:00+00:00"
  ```
  > **_NOTE:_** An example is provided in [FireSat+ YAML configuration file](examples/firesat/firesat.yaml).
- Introduced `get_app_specific_config()` in `configuration.py` that retrieves application-specific configuration from the `execution.managed_applications` section based on the application name.
- Added `application_configuration` to `config.rc` (runtime configuration) at `configuration.py`, which contains user-provided, application-specific configurations. These application-specific configurations can be defined for each application within the YAML configuration file at the field `execution.managed_applications.<application name>.configuration_parameters`. This replaces `config.py` for each application in the NOS-T Tools examples.

Changed:
- Moved `self.establish_exchange()` from `self._execute_test_plan_impl()` to `self.start_up()` to prevent execution from starting before RabbitMQ exchanges have been declared and resulting in an error.
- Removed conditional check for `self.app.channel.is_open` and `self.app.connection.is_open` in `application_utils.py` before sending status messages; now assumes connection is always valid or managed externally.
- Refactored the FireSat+, Downlink, Scalability, and scienceDash test suites to:
  - Use a unified YAML configuration file per example
  - Define application-specific settings under the `execution.managed_applications.<application name>.configuration_parameters` field instead of the previous `config.py`
  - Improve general code structure for enhanced efficiency, readability, and user experience
- Updated documentation for the FireSat+, Downlink, Scalability, and scienceDash test suites.

## 2.2.1
Added:
- Introduced a boolean `setup_signal_handlers` (default=True) parameter for Application() class, which makes `self._setup_signal_handlers()` conditional. This prevents errors in nost-manager-backend. 
  - Added `setup_signal_handlers` argument (default=True) to `__init__` of `Manager` and `ManagedApplication` classes.
- Added `yaml_file` section to `RuntimeConfig` in both `schemas.py` and `configuration.py`. This attribute holds the path to YAML configuration file if provided; otherwise, it defaults to `None`.
- Introduced `_get_parameters_from_config()` in `Application`, `Manager`, and `ManagedApplication` to facilitate getting the application parameters from the YAML configuration or user-provided arguments based on `self.config.rc.yaml_file` being None or not. 
- Added `keycloak_authentication` argument to `__init__()` of `ConnectionConfig` class (default=False).
- Implemented `start_wallclock_refresh_thread()` which periodically updates the wallclock offset. 
- Added `WallclockOffsetProperties` to `schemas.py` that contains `wallclock_offset_refresh_interval` and `ntp_host` fields used in `start_wallclock_refresh_thread()`

Updated:
- Made `general` section of `ExecConfig` optional in `schemas.py`for situations where YAML configuration file is not provided.
- Made `client_id` and `client_secret_key` in `Credentials` default to None.
- Changed `parameters.time_scale_updates` reference to `self.time_scale_updates` in `manager.py`.
- Updated code in `start_up()` related to definition of parameters to use `_get_parameters_from_config()` subclasses to customize parameter retrieval in:
  - `Application` class of `application.py`
  - `Manager` class of `manager.py`
  - `ManagedApplication` class of `managed_application.py` 
- Updated `self.simulator.set_end_time(sim_stop_time)` from `stop()` in `manager.py` to run only if `self.simulator.get_mode() == Mode.EXECUTING`
- Removed `time_step` and `manager_app_name` arguments from `start_up()` in `Manager` class
- Modified `set_wallclock_offset()` in `simulator.py` to allow setting wallclock offset when in `Mode.EXECUTING`