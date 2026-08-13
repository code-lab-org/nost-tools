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

## 2.3.0
Added:
- Introduced a boolean `setup_signal_handlers` (default=True) parameter for Application() class, which makes `self._setup_signal_handlers()` conditional. This prevents errors in nost-manager-backend. 
  - Added `setup_signal_handlers` argument (default=True) to `__init__` of `Manager` and `ManagedApplication` classes.
- Added `yaml_file` section to `RuntimeConfig` in both `schemas.py` and `configuration.py`. This attribute holds the path to YAML configuration file if provided; otherwise, it defaults to `None`.
- Introduced `_get_parameters_from_config()` in `Application`, `Manager`, and `ManagedApplication` to facilitate getting the application parameters from the YAML configuration or user-provided arguments based on `self.config.rc.yaml_file` being None or not. 
- Added `keycloak_authentication` argument to `__init__()` of `ConnectionConfig` class (default=False).
- Implemented `start_wallclock_refresh_thread()` which periodically updates the wallclock offset. 
- Added `WallclockOffsetProperties` to `schemas.py` that contains `wallclock_offset_refresh_interval` and `ntp_host` fields used in `start_wallclock_refresh_thread()`
- Implemented `is_scenario_time_step` in `ManagerConfig` class, similar to that of `ManagedApplicationConfig`

Updated:
- Made `general` section of `ExecConfig` optional in `schemas.py`for situations where YAML configuration file is not provided.
- Made `client_id` and `client_secret_key` in `Credentials` default to None.
- Changed `parameters.time_scale_updates` reference to `self.time_scale_updates` in `manager.py`.
- Updated code in `start_up()` related to the definition of parameters to use `_get_parameters_from_config()` subclasses to customize parameter retrieval in:
  - `Application` class of `application.py`
  - `Manager` class of `manager.py`
  - `ManagedApplication` class of `managed_application.py` 
- Updated `self.simulator.set_end_time(sim_stop_time)` from `stop()` in `manager.py` to run only if `self.simulator.get_mode() == Mode.EXECUTING`
- Removed `time_step` and `manager_app_name` arguments from `start_up()` in `Manager` class
- Modified `set_wallclock_offset()` in `simulator.py` to allow setting wallclock offset when in `Mode.EXECUTING`
- Update default value of `time_status_init` to `datetime.now()` in `ApplicationConfig` class

## 2.4.0
Added:
- Introduced the `configure_file_logging()` method in the base `Application` class, automatically invoked during the `start_up()` process.
- Added a `LoggingConfig` Pydantic model to encapsulate configuration parameters for the `configure_file_logging()` method.

Updated:
- Changed the default value of `token_refresh_interval` in the `KeycloakConfig` Pydantic class from 60 seconds (1 minute) to 240 seconds (4 minutes).

## 3.0.0
Added:
- Added comprehensive freeze time tracking system and callbacks in `Manager` class in `manager.py` to properly account for dynamic, distributed freezes, resumes, and updates to scenario time:
  - Added `on_freeze_request()` callback which freezes scenario time based on messages containing requests from managed applications, integrated this callback into `start_up()` method
  - Added `_handle_freeze_request()` that handles dynamic, distributed freeze requests
  - Added `freeze()` that issues freeze command, integrated this into the `_handle_freeze_request()`
  - Added `on_resume_request()` callback which resumes scenario time based on messages containing requests from managed applications, integrated this callback into `start_up()` method
  - Added `on_update_request()` callback which updates the time scale factor based on messages containing requests from managed applications, integrated this callback into `start_up()` method
  - Added `update()` that issues update command, integrated this into the `on_update_request()` method
- Added new methods to `ManagedApplication` class in `managed_application.py` to allow requests for a freeze in scenario time from the `Manager` class in `manager.py`
  - Added `request_freeze()` method that sends a FreezeRequest message which is received by the `Manager` application, added an associated `on_manager_freeze()` callback that responds to FreezeCommand messages from `Manger`
  - Added `request_resume()` method that sends a ResumeRequest message which is received by the `Manager` application, added an associated `on_manager_resume()` callback that responds to ResumeCommand messages from `Manager`
  - Added `request_update()` method that sends a UpdateRequest message which is received by the `Manager` application, added an associated `on_manager_update()` callback that responds to UpdateCommand messages from `Manager`
- Added new freeze-tracking capabilities to `Simulator` class in `simulator.py`
  - Added reset of wallclock and simulation epochs when mode switches to Mode.EXECUTING in `_wait_for_tock()` method
- Added the following classes to `schemas.py`:
  - `FreezeTaskingParameters`, `FreezeCommand`, `ResumeTaskingParameters`, `ResumeCommand`, `FreezeRequestParameters`, `FreezeRequest`, `ResumeRequestParameters`, `ResumeRequest`, `UpdateRequestParameters`, `UpdateRequest`

Updated:
- Removed code related to scheduled time scale updates in `_execute_test_plan_impl()` of `Manager` application. Scheduled time scale factor updates, defined in the YAML configuration file, are no longer supported. They must now be requested by a `ManagedApplication` and processed by the `Manager` who maintains control of sending the `FreezeCommand` as defined in `schemas.py`
- Removed `TimeScaleUpdate` class in `manager.py`
- Removed `TimeScaleUpdateSchema` and `FreezeSchema` classes in `schemas.py`
- Removed `time_scale_updates` and `freezes` fields from `ManagerConfig` class in `schemas.py`
- Prevent re-entrant execution in `Simulator.execute()` by adding an explicit mode guard; now raises a clear `RuntimeError` when called outside `UNDEFINED`, `INITIALIZED`, or `TERMINATED` modes: `Cannot execute: simulator is {self._mode}. Wait for TERMINATED or terminate the current run.`
- Removed `WallclockOffsetProperties` class and `wallclock_offset_properties` section from `RuntimeConfig` in `schemas.py` and `configuration.py`.
- Added `wallclock_offset_refresh_interval` and `ntp_host` to `GeneralConfig` class in `schemas.py`
- Updated FireSat test suite to show examples of time scale updates and scenario time freezes.

## 3.0.1
Updated:
- Removed the calculation of `target_resume_time` from the `freeze()` method in `manager.py`.
A freeze event now persists until the resume time specified in the `FreezeCommand` message payload is reached. Previously, the resume time was calculated from the scenario time at which the `FreezeRequest` message was received by the manager (scenario time at message receipt + freeze duration), which could cause time drift.
- Prevented a one-step early advance after RESUMING by ensuring the `_wait_for_tock()` method in `simulator.py` re-anchors epochs and waits until the next tick before advancing.
- Updated the `on_manager_freeze()` method in `managed_application.py` to honor `simFreezeTime` from a `FreezeCommand`, aligning to the requested scenario time (via wallclock mapping) before calling `pause()` so all apps freeze at the same scenario time.

## 3.0.2
Updated:
- Removed `self._next_time = self._time` from `resume()` in `simulator.py`, which was causing a drift of approximately 1 second per simulated day.
- Changed a log statement in `freeze()` within `manager.py` from log.info to log.debug to reduce verbosity. The affected line reports the remaining time during a freeze.

## 3.0.3
Added:
- **Service Account Authentication Support**: Applications can now authenticate with Keycloak using service accounts (client credentials only) without requiring username and password. This is ideal for automated systems, scripts, and long-running processes.
- **Dual Authentication Modes**: The system now supports two Keycloak authentication modes:
  - **User Account**: Requires `USERNAME`, `PASSWORD`, `CLIENT_ID`, and `CLIENT_SECRET_KEY`
  - **Service Account**: Requires only `CLIENT_ID` and `CLIENT_SECRET_KEY`
- **Intelligent OTP Detection**: Added smart OTP/TOTP requirement detection in `new_access_token()` method that:
  - Analyzes Keycloak error responses for OTP-related keywords (`otp`, `totp`, `two-factor`, `2fa`, `mfa`)
  - Only prompts for OTP when Keycloak explicitly indicates it's required
  - Prevents false OTP prompts when username/password are incorrect
  - Provides clear, context-specific error messages for different failure scenarios
- **Programmatic OTP Support**: Added optional `otp` parameter to `new_access_token()` method to support automation with OTP-enabled accounts
- **Credentials Validation**: Added `validate_authentication_mode()` validator in `Credentials` schema that enforces valid credential combinations and provides clear error messages for invalid configurations
- **Comprehensive Test Suite**: Added `tests/test_credentials.py` with 7 tests covering both authentication modes and validation scenarios
- **Documentation**:
  - Created `KEYCLOAK_AUTH_MODES.md` with detailed guide on both authentication modes, setup instructions, and error handling
  - Created `OTP_IMPROVEMENTS.md` documenting intelligent OTP handling improvements
  - Created `.env.example` template showing both authentication modes
  - Created `.env.sos.example` specific template for sos.yaml configuration

Changed:
- **Credentials Schema** (`schemas.py`): Changed default values for `username` and `password` from `"admin"` to `None` to make them optional for service account authentication
- **Environment Variable Loading** (`configuration.py`): Updated `load_environment_variables()` method to support optional username/password when Keycloak authentication is enabled, allowing service account mode
- **Authentication Method** (`application.py`): Updated `new_access_token()` method to:
  - Automatically detect authentication mode based on presence of username/password
  - Use `grant_type="password"` for user authentication
  - Use `grant_type=["client_credentials"]` for service account authentication
  - Intelligently handle OTP requirements with proper error detection
  - Log which authentication mode is being used for debugging
- **Error Messages**: Improved authentication error messages to clearly indicate:
  - "Authentication failed. Please check your username and password" for wrong credentials
  - "OTP/TOTP is required for this account" when OTP is needed
  - "The provided OTP may be incorrect or expired" for wrong OTP

## 3.0.4
Added:
- **Basic Authentication Mode**: Added support for localhost/development connections without Keycloak authentication
  - Allows `USERNAME` + `PASSWORD` only (no client credentials required)
  - Ideal for local RabbitMQ development without Keycloak infrastructure
  - System now supports three distinct authentication modes instead of two
- **Enhanced Credentials Validation**: Updated `validate_authentication_mode()` in `Credentials` schema to support three authentication modes:
  - **Basic Auth (localhost)**: `USERNAME` + `PASSWORD` only
  - **Keycloak Service Account**: `CLIENT_ID` + `CLIENT_SECRET_KEY` only
  - **Keycloak User Account**: `USERNAME` + `PASSWORD` + `CLIENT_ID` + `CLIENT_SECRET_KEY`
- **Comprehensive Three-Mode Testing**: Added `test_basic_auth_mode_valid()` test to verify localhost authentication works correctly
- **Optional Scenario Time and Tolerance for ResumeRequest**: Added optional fields to `ResumeRequestParameters` in `schemas.py`:
  - `sim_resume_time`: Allows managed applications to specify target scenario time for resume
  - `tolerance`: Time tolerance (timedelta) for matching scenario time to requested time
  - Both fields are optional and maintain backward compatibility (default to `None`)
  - Uses `simResumeTime` and `tolerance` aliases for JSON serialization consistency
- **Tolerance-Based Resume Command Logic**: Added `_handle_resume_request()` method in `manager.py` to handle tolerance-based resume requests:
  - Runs in a separate thread to avoid blocking message callbacks
  - Default tolerance of 12 hours can be specified by managed applications

Changed:
- **Credentials Validator** (`schemas.py`): Enhanced validation logic to recognize basic authentication as a valid mode alongside Keycloak authentication modes
- **Test Suite** (`tests/test_credentials.py`):
  - Renamed `test_user_account_mode_valid()` to `test_keycloak_user_account_mode_valid()` for clarity
  - Updated test assertions to match new error messages
  - Now testing 8 scenarios (was 7) including basic auth mode
- **Error Messages**: Updated validation error messages to include all three authentication modes for better troubleshooting
- **Resume Request Handling** (`manager.py`): Modified `on_resume_request()` to delegate to `_handle_resume_request()` for tolerance-based handling:
  - **If `tolerance` is NOT provided**: `ResumeCommand` is sent immediately (regardless of `sim_resume_time`)
  - **If `tolerance` IS provided**:
    - **Both `tolerance` and `sim_resume_time` provided**: Checks if current scenario time is within tolerance of requested time
      - **Within tolerance**: `ResumeCommand` is sent immediately
      - **Outside tolerance**: Request is ignored with informative log message showing time difference
    - **Only `tolerance` provided (no `sim_resume_time`)**: `ResumeCommand` is sent immediately
  - This tolerance-based approach allows managed applications to send multiple `ResumeRequest` messages with the Manager only acting when scenario time is within the specified tolerance window
- **Exchange Declaration** (`application.py`): Moved `establish_exchange()` method from `Manager` class to base `Application` class:
  - All applications (unmanaged Application, ManagedApplication, and Manager) now automatically declare the exchange when channel opens
  - Fixes "NOT_FOUND - no exchange" errors when unmanaged applications try to publish messages
  - Exchange is declared in `on_channel_open()` callback, ensuring it exists before any message operations
  - Eliminates requirement for Manager to run first before other applications can send messages
- **Freeze Request Logging** (`manager.py`): Fixed misleading log message in `_handle_freeze_request()`:
  - "Indefinite freeze requested - manual resume required" now logs before freeze starts (not after)
  - Added "Indefinite freeze has ended" log message after freeze completes
- **BasicProperties Handling** (`application.py`): Fixed RabbitMQ protocol error "UNEXPECTED_FRAME - expected content header for class 60":
  - Added `_build_basic_properties()` helper method that filters out `None` values before creating `pika.BasicProperties`
  - Updated `send_message()` and `_process_message_queue()` to use the new helper
  - Prevents protocol errors when YAML configuration has undefined/None BasicProperties fields
  - Resolves random connection drops with error code 505 (UNEXPECTED_FRAME)

## 3.0.5
Added:
- **Application Configuration Support**: Added `configuration_parameters` support for unmanaged `Application` class:
  - Updated `ExecConfig` in `schemas.py` to include `applications` dictionary (similar to `managed_applications`)
  - Updated `ApplicationConfig` in `schemas.py` to include `configuration_parameters` field
  - Updated `get_app_specific_config()` in `configuration.py` to accept `app_type` parameter ("applications" or "managed_applications")
  - Updated `Application._get_parameters_from_config()` to retrieve app-specific config from `applications` section
  - Updated `ConnectionConfig` to populate `application_configuration` from both `applications` and `managed_applications` sections
  - Enables custom per-application configuration parameters in YAML
- **Resume Tolerance Configuration**: Added global `resume_tolerance` parameter to `GeneralConfig`:
  - Added `request_resume()` method to `Application` class that sends `ResumeRequest` messages with optional `sim_resume_time` and `tolerance` parameters
  - Removed duplicate `request_resume()` from `ManagedApplication` - now inherits enhanced version from `Application`
  - Default tolerance of 12 hours can be configured globally in `execution.general.resume_tolerance`
  - Can be overridden per-request by passing `tolerance` parameter to `request_resume()`
  - Example YAML structure:
    ```yaml
    execution:
      general:
        prefix: nost
        resume_tolerance: "12:00:00"  # Global default for all applications
    ```

## 3.0.6
Changed:
- **Consumer Cleanup on Shutdown** (`application.py`): Removed redundant `stop_consuming()` call in `stop_application()`:
  - Queue deletion already implicitly cancels all consumers attached to those queues via RabbitMQ's standard behavior
  - Eliminates "pika.channel: basic_cancel - consumer not found" warning during application shutdown
  - Reduces unnecessary RPC calls during cleanup sequence

- **Reconnection Logic** (`application.py`): Fixed network reconnection failing when applications are in frozen/paused state:
  - Removed duplicate `_io_thread` creation in `reconnect()` method that caused two threads to compete for the same ioloop
  - Now stops the old ioloop explicitly after creating the new connection, allowing `_start_io_loop`'s while loop to pick up the new
  connection naturally
  - Changed error handler to use `threading.Timer` instead of `ioloop.call_later()` for retry scheduling, since ioloop state may be
inconsistent during failures
  - Reconnection now works reliably regardless of simulator mode (executing, paused, etc.)

## 3.0.7
Changed:
- **Python-Keycloak Version Constraint**: Pinned `python-keycloak` dependency to `>=5, <7` in `pyproject.toml`:
  - Version 7.0.0+ uses PEP 604 union type syntax (`str | Role`) which requires Python 3.10+
  - This constraint maintains compatibility with Python 3.9 (`requires-python = ">=3.9"`)
  - Can be relaxed when `nost_tools` drops Python 3.9 support or upstream adds `from __future__ import annotations`

## 3.0.8
Fixed:
- **Manager Stop Command Timing During Freezes** (`manager.py`): Fixed bug where Manager sent Stop command at the originally expected time instead of accounting for freeze duration:
  - Added pause mode check in `_execute_test_plan_impl()` waiting loop to skip stop time calculations while simulator is in `PAUSED` or `PAUSING` mode
  - Prevents race condition where stale `_wallclock_epoch` and `_simulation_epoch` values caused incorrect stop time calculations during freezes
  - Stop command now correctly sent at `original_expected_time + freeze_duration` (e.g., 10 minutes total wallclock time for 5-minute execution + 5-minute freeze)
  - Ensures proper synchronization between Manager's waiting logic and Simulator's freeze/resume cycle

## 3.0.9
Changed:
- **ScenarioTimeIntervalCallback Initial Offset** (`observer.py`): Added optional `time_init` parameter to `ScenarioTimeIntervalCallback` to decouple the initial trigger offset from the repeating interval:
  - Previously, the initial offset and repeating interval were always the same value, causing cumulative drift when the interval was not exactly 24 hours (e.g., `timedelta(hours=23, minutes=55)` drifted 5 minutes earlier each day)
  - New `time_init` parameter sets the offset for the first trigger independently from `time_interval`
  - When omitted, defaults to `time_interval` (backward compatible)
  - Example: `ScenarioTimeIntervalCallback(callback, timedelta(days=1), time_init=timedelta(hours=23, minutes=55))` fires at 23:55 daily without drift

## 3.1.0
Added:
- **Pre-acquired Token Authentication Mode** (`application.py`, `manager.py`, `managed_application.py`): Added optional `access_token` and `refresh_token` keyword arguments to `Application.start_up()`, `Manager.start_up()`, and `ManagedApplication.start_up()`:
  - Enables a third Keycloak authentication mode, complementing existing user (username/password) and service account (client_credentials) modes
  - When both tokens are provided, `start_up()` skips the Keycloak grant and uses the pre-acquired tokens directly to authenticate the RabbitMQ connection
  - The existing background refresh thread continues to renew the session by calling Keycloak's refresh endpoint with the forwarded refresh token — works for public clients without a `client_secret_key`
  - Intended for server-side components (e.g., a backend API) that receive user tokens from an authenticated frontend and need to act on behalf of that user against RabbitMQ, preserving per-user broker scope enforcement
  - Raises `ValueError` if `access_token` is provided without `refresh_token`, since the refresh thread requires a refresh token to keep the session alive
  - Fully backwards-compatible: existing callers that do not pass the new kwargs retain identical behavior

Changed:
- **Initial Refresh Token Capture** (`application.py`): In the default Keycloak authentication path, `start_up()` now captures the refresh token returned from the initial `new_access_token()` call and stores it on `self.refresh_token` before starting the refresh thread:
  - Previously, the returned refresh token was discarded, causing the refresh thread's first tick to perform a redundant full grant
  - No behavior change for callers; removes one unnecessary Keycloak round-trip during startup

## 3.2.0
Fixed:
- **TLS Certificate Verification** (`application.py`, `schemas.py`): TLS connections to RabbitMQ and Keycloak now verify the server's certificate against the system trust store and confirm that it matches the configured host. Upgrading is recommended for all deployments that connect over TLS.

Added:
- **`tls_ca_cert` Configuration Field** (`schemas.py`): Added optional `tls_ca_cert` to `RabbitMQConfig` and `KeycloakConfig` for self-hosted servers presenting self-signed or privately-signed certificates:
  - When unset, the system trust store is used, which covers publicly-trusted certificates and requires no configuration
  - When set, the named file replaces the system trust store for that connection; a self-signed certificate may be supplied directly, since it is its own trust anchor
  - Applied per server, so a self-hosted RabbitMQ broker and a NASA-hosted Keycloak server are configured independently
- **Certificate Failure Guidance** (`application.py`): `on_connection_error()` now detects certificate verification failures and logs the `tls_ca_cert` setting to add, the `subjectAltName` requirement, and an `openssl` command that generates a matching certificate

Changed:
- **RabbitMQ SSL Context** (`application.py`): Rebuilt the SSL context using `ssl.create_default_context()`, and now passes `server_hostname` to `pika.SSLOptions` to enable Server Name Indication (SNI) and hostname verification:
  - TLS 1.3 is now negotiated where the server supports it; connections were previously pinned to TLS 1.2
  - Removed a cipher restriction that excluded servers presenting ECDSA certificates and had no effect on TLS 1.3 cipher suites
- **TLS Startup Log** (`application.py`): The `Using TLS/SSL.` message now names the trust anchor in use, either the system trust store or the configured `tls_ca_cert` path

Removed:
- **Global Warning Suppression** (`application.py`): Removed a module-level `urllib3` warning filter that silenced insecure-request warnings process-wide for every library loaded alongside NOS-T Tools

Upgrade Notes:
- No configuration change is required for the NOS-T broker, the NASA-hosted Keycloak server, or a local broker running without TLS
- A self-hosted server presenting a self-signed or privately-signed certificate requires `tls_ca_cert`; see the TLS Certificate Verification section of the YAML configuration documentation

## 3.3.0
Fixed:
- **Thread-Safe Message Publishing** (`application.py`): Fixed RabbitMQ `505 UNEXPECTED_FRAME` errors caused by concurrent `basic_publish` calls from multiple threads interleaving AMQP frames on the wire:
  - Added `_do_publish()`, which performs `basic_publish` exclusively on pika's IO thread
  - Refactored `send_message()` to schedule publishes via `connection.ioloop.add_callback_threadsafe()` rather than calling `basic_publish` directly
  - Added a `threading.Lock` (`_queue_lock`) protecting `_message_queue` against concurrent access
  - Moved `_message_queue` initialization from a lazy `hasattr` check to eager initialization in `__init__`
- **Message Ordering After a Failed Publish** (`application.py`): A message re-queued after a failed publish now retains the timestamp from when it was originally submitted:
  - The queue is drained in timestamp order, so re-stamping a message on failure allowed it to be delivered after messages submitted later
- **Silent Message Loss** (`application.py`): The publish paths now log an error when a message is discarded because the queue is full, and a warning when scheduling queued-message processing fails:
  - Previously these paths discarded messages with no log entry, leaving no indication that a message was never delivered

Added:
- **Pending Message Flush on Shutdown** (`application.py`): `stop_application()` now waits for publishes already scheduled on the IO thread to complete before deleting exchanges and queues:
  - Because publishing is asynchronous, messages submitted immediately before shutdown could otherwise be discarded when the IO loop stopped
  - Waits up to 5 seconds, then logs a warning and proceeds rather than blocking shutdown indefinitely
  - Returns immediately when the connection is already closed, or when called from the IO thread itself
- **Application Test Coverage** (`tests/test_application.py`): Added 11 tests covering message publishing, queueing, and shutdown behavior:
  - Verifies routing key construction, multi-topic sends, queueing while disconnected, queue-full handling, first-in first-out flush on reconnect, and timestamp preservation across re-queues
  - Asserts that `send_message()` schedules publishes rather than performing them inline, guarding against reintroducing the concurrency defect

Upgrade Notes:
- `send_message()` returns once a publish has been scheduled, not once it has been written to the broker. Its signature is unchanged and existing callers require no modification, but code depending on a message reaching the broker before `send_message()` returns should account for the new timing
- Applications that shut down immediately after sending are covered by the flush described above

## 3.3.1
Fixed:
- **Keycloak Server Address in Documentation** (`example.yml`, `yml_file.rst`, `authentication_modes.rst`): Corrected the Keycloak host and port in every published configuration example, which named the RabbitMQ broker rather than the Keycloak server:
  - The documented endpoint drops packets rather than refusing them, so a configuration copied from the examples produced a silent hang until the socket timeout expired, with no error indicating the cause
  - `authentication_modes.rst` carried the same values in the section describing how to configure Keycloak authentication
- **Interval Publishers Attached to a Running Simulator** (`publisher.py`): `ScenarioTimeIntervalPublisher` and `WallclockTimeIntervalPublisher` now seed their next publish time when a scenario time change arrives before the simulator reaches `INITIALIZED`:
  - Both previously compared an unset value against a datetime and raised `TypeError`
  - Reachable only when a publisher is added to an already-running simulator; the equivalent classes in `observer.py` already handled this
- **Deprecated Pydantic Method** (`configuration.py`): Replaced `BaseModel.copy()` with `model_copy()`, removed in Pydantic V3:
  - Emitted a deprecation warning on every configuration load
  - Behavior is unchanged; the copy remains shallow and independent at the top level

Changed:
- **`set_wallclock_offset` Documentation** (`simulator.py`): Corrected the docstring, which stated the method requires `UNDEFINED`, `INITIALIZING`, `INITIALIZED`, or `TERMINATED` mode. The implementation has only ever rejected `TERMINATING`, and applications refresh the offset periodically to correct clock drift while a scenario is executing:
  - No behavior change; the documented restriction never existed in the code
  - Included in this release because it was corrected after 3.3.0 was tagged
- **Solace Certificate Guide Marked Legacy** (`certificate_authorization.rst`): The client certificate guide describes Solace, the message broker used before RabbitMQ, and none of its procedures apply to the current stack. It now opens with a notice to that effect and links to the TLS Certificate Verification section of the YAML configuration guide.
- **Test Coverage** (`tests/`): Expanded the test suite from 44 to 114 tests and overall coverage from 36% to 48%, added end-to-end tests that run against a real RabbitMQ broker and skip when none is reachable, and fixed two tests that failed or intermittently flaked. Not part of the distributed package; recorded here as a record of repository state at this release.