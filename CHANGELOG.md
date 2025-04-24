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
Addded: 
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