"""
Provides a base manager that coordinates a distributed scenario execution.
"""

import json
import logging
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import List

from pydantic import ValidationError

from .application import Application
from .application_utils import ConnectionConfig
from .schemas import (
    FreezeCommand,
    FreezeRequest,
    InitCommand,
    ReadyStatus,
    ResumeCommand,
    ResumeRequest,
    StartCommand,
    StopCommand,
    TimeStatus,
    UpdateCommand,
)
from .simulator import Mode

logger = logging.getLogger(__name__)


class TimeScaleUpdate(object):
    """
    Provides a scheduled update to the simulation time scale factor by sending a message at the designated sim_update_time
    to change the time_scale_factor to the indicated value.

    Attributes:
        time_scale_factor (float): scenario seconds per wallclock second
        sim_update_time (:obj:`datetime`): scenario time that the update will occur
    """

    def __init__(self, time_scale_factor: float, sim_update_time: datetime):
        """
        Instantiates a new time scale update.

        Args:
            time_scale_factor (float): scenario seconds per wallclock second
            sim_update_time (:obj:`datetime`): scenario time that the update will occur
        """
        self.time_scale_factor = time_scale_factor
        self.sim_update_time = sim_update_time


class Freeze(object):
    """
    Represents a scheduled freeze of the simulation.
    """

    def __init__(self, sim_freeze_time: datetime, freeze_duration: timedelta = None):
        """
        Instantiates a new freeze.

        Args:
            sim_freeze_time (:obj:`datetime`): scenario time that the freeze will occur
            freeze_duration (:obj:`timedelta`, optional): wallclock time duration for which to freeze. If None, creates an indefinite freeze.
        """
        self.sim_freeze_time = sim_freeze_time
        self.freeze_duration = freeze_duration

    @property
    def is_indefinite(self) -> bool:
        """Returns True if this is an indefinite freeze (no duration specified)."""
        return self.freeze_duration is None

    @property
    def is_timed(self) -> bool:
        """Returns True if this is a timed freeze (duration specified)."""
        return self.freeze_duration is not None


class Manager(Application):
    """
    NOS-T Manager Application.

    This object class defines a manager to orchestrate test run executions.

    Attributes:
        prefix (str): The test run namespace (prefix)
        simulator (:obj:`Simulator`): Application simulator
        client (:obj:`Client`): Application MQTT client
        time_step (:obj:`timedelta`): Scenario time step used in execution
        time_status_step (:obj:`timedelta`): Scenario duration between time status messages
        time_status_init (:obj:`datetime`): Scenario time of first time status message
        app_name (str): Test run application name
        app_description (str): Test run application description (optional)
        required_apps_status (dict): Ready status for all required applications
    """

    def __init__(
        self,
        app_name: str = "manager",
        app_description: str = None,
        setup_signal_handlers: bool = True,
    ):
        """
        Initializes a new manager.

        Attributes:
            setup_signal_handlers (bool): whether to set up signal handlers (default: True)
        """
        # call super class constructor
        super().__init__(
            app_name, app_description, setup_signal_handlers=setup_signal_handlers
        )
        self.required_apps_status = {}
        # Add instance variable to track total freeze time
        self.total_freeze_time = timedelta(0)
        self._freeze_time_updated = threading.Event()
        self._freeze_time_lock = threading.Lock()

        self.sim_start_time = None
        self.sim_stop_time = None
        start_time = None
        time_step = None
        time_scale_factor = None
        time_scale_updates = None
        time_status_step = None
        time_status_init = None
        command_lead = None
        required_apps = None
        init_retry_delay_s = None
        init_max_retry = None

    def establish_exchange(self):
        """
        Establishes the exchange for the manager application.
        """
        self.channel.exchange_declare(
            exchange=self.prefix,
            exchange_type="topic",
            durable=True,
            auto_delete=True,
        )

    def _sleep_with_heartbeat(self, total_seconds):
        """
        Sleep for a specified number of seconds while allowing connection heartbeats.
        Works with SelectConnection by using short sleep intervals.

        Args:
            total_seconds (float): Total number of seconds to sleep
        """
        if total_seconds <= 0:
            return

        # Sleep in smaller chunks to allow heartbeats to pass through
        check_interval = 30  # Check every 30 seconds at most
        end_time = time.time() + total_seconds

        logger.debug(f"Starting heartbeat-safe sleep for {total_seconds:.2f} seconds")

        while time.time() < end_time:
            # Calculate remaining time
            remaining = end_time - time.time()

            # Sleep for the shorter of check_interval or remaining time
            sleep_time = min(check_interval, remaining)

            if sleep_time > 0:
                time.sleep(sleep_time)
                logger.debug(
                    f"Heartbeat check: {remaining:.2f} seconds remaining in sleep"
                )

    def _get_parameters_from_config(self):
        """
        Override to get parameters specific to manager application

        Returns:
            object: Configuration parameters for the manager application
        """
        if self.config and self.config.rc.yaml_file:
            try:
                return getattr(
                    self.config.rc.simulation_configuration.execution_parameters,
                    "manager",
                    None,
                )
            except (AttributeError, KeyError):
                return None
        return None

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = True,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = False,
    ) -> None:
        """
        Starts up the application by connecting to message broker, starting a background event loop,
        subscribing to manager events, and registering callback functions.

        Args:
            prefix (str): execution namespace (prefix)
            config (:obj:`ConnectionConfig`): connection configuration
            set_offset (bool): True, if the system clock offset shall be set using a NTP request prior to execution
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time for first time status message
            shut_down_when_terminated (bool): True, if the application should shut down when the simulation is terminated
        """
        self.config = config

        # Call base start_up to handle common parameters
        super().start_up(
            prefix,
            config,
            set_offset,
            time_status_step,
            time_status_init,
            shut_down_when_terminated,
        )

        # Additional manager-specific setup: establish the exchange
        self.establish_exchange()

        # Add callbacks for freeze/resume requests from managed applications
        self.add_message_callback("*", "request.freeze", self.on_freeze_request)
        self.add_message_callback("*", "request.resume", self.on_resume_request)

    def on_freeze_request(self, ch, method, properties, body) -> None:
        """
        Callback to handle freeze requests from managed applications.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # Parse the freeze request
            message = body.decode("utf-8")
            freeze_request = FreezeRequest.model_validate_json(message)
            params = freeze_request.tasking_parameters

            logger.info(
                f"Received freeze request from {params.requesting_app}: {message}"
            )

            # Use a separate thread to handle the freeze to avoid blocking the callback
            freeze_thread = threading.Thread(
                target=self._handle_freeze_request,
                args=(params.freeze_duration, params.sim_freeze_time),
                daemon=True,
            )
            freeze_thread.start()

        except ValidationError as e:
            logger.error(f"Validation error in freeze request: {e}")
        except Exception as e:
            logger.error(
                f"Exception handling freeze request (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def _handle_freeze_request(
        self, freeze_duration: timedelta = None, sim_freeze_time: datetime = None
    ) -> None:
        try:
            if freeze_duration is not None:
                logger.info(
                    f"Handling timed freeze request for duration: {freeze_duration}, "
                    f"sim_freeze_time: {sim_freeze_time}"
                )

                # Use the original freeze method with duration - it handles timing internally
                self.freeze(freeze_duration, sim_freeze_time)

                # The freeze method blocks until completion, so now we can safely resume
                self.resume()

                # Add the freeze duration to our total freeze time AFTER the freeze completes
                with self._freeze_time_lock:
                    self.total_freeze_time += freeze_duration
                    self._freeze_time_updated.set()  # Signal that freeze time was updated

                logger.info(
                    f"Completed freeze of duration {freeze_duration}. Total freeze time now: {self.total_freeze_time}"
                )

            else:
                # For indefinite freezes, just freeze (requires manual resume)
                self.freeze(None, sim_freeze_time)
                logger.info("Indefinite freeze requested - manual resume required")

        except Exception as e:
            logger.error(f"Error handling freeze request: {e}")
            print(traceback.format_exc())

    def on_resume_request(self, ch, method, properties, body) -> None:
        """
        Callback to handle resume requests from managed applications.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # Parse the resume request
            message = body.decode("utf-8")
            resume_request = ResumeRequest.model_validate_json(message)
            params = resume_request.tasking_parameters

            logger.info(
                f"Received resume request from {params.requesting_app}: {message}"
            )

            # Execute the resume command
            self.resume()

        except ValidationError as e:
            logger.error(f"Validation error in resume request: {e}")
        except Exception as e:
            logger.error(
                f"Exception handling resume request (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def execute_test_plan(self, *args, **kwargs) -> None:
        """
        Starts the test plan execution in a background thread.

        Args:
            *args: Positional arguments to be passed to the test plan execution.
            **kwargs: Keyword arguments to be passed to the test plan execution.
        """
        thread = threading.Thread(
            target=self._execute_test_plan_impl, args=args, kwargs=kwargs, daemon=True
        )
        logger.debug("Running test plan in background thread.")
        thread.start()

    def _execute_test_plan_impl(
        self,
        sim_start_time: datetime = None,
        sim_stop_time: datetime = None,
        start_time: datetime = None,
        time_step: timedelta = timedelta(seconds=1),
        time_scale_factor: float = 1.0,
        time_scale_updates: List[TimeScaleUpdate] = [],
        freezes: List[Freeze] = [],
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        command_lead: timedelta = timedelta(seconds=0),
        required_apps: List[str] = [],
        init_retry_delay_s: int = 5,
        init_max_retry: int = 5,
    ) -> None:
        """
        A comprehensive command to start a test run execution.

        Publishes an initialize, start, zero or more updates, and a stop message in one condensed JSON script for testing purposes,
        or consistent test-case runs.

        Args:
            sim_start_time (:obj:`datetime`): scenario time at which to start execution
            sim_stop_time (:obj:`datetime`): scenario time at which to stop execution
            start_time (:obj:`datetime`): wallclock time at which to start execution (default: now)
            time_step (:obj:`timedelta`): scenario time step used in execution (default: 1 second)
            time_scale_factor (float): scenario seconds per wallclock second (default: 1.0)
            time_scale_updates (list(:obj:`TimeScaleUpdate`)): list of scheduled time scale updates (default: [])
            freezes (list(:obj:`Freeze`)): list of scheduled freezes (default: [])
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time of first time status message
            command_lead (:obj:`timedelta`): wallclock lead time between command and action (default: 0 seconds)
            required_apps (list(str)): list of application names required to continue with the execution
            init_retry_delay_s (float): number of seconds to wait between initialization commands while waiting for required applications
            init_max_retry (int): number of initialization commands while waiting for required applications before continuing to execution
        """
        if self.config.rc.yaml_file:
            logger.info(
                f"Collecting execution parameters from YAML configuration file: {self.config.rc.yaml_file}"
            )
            parameters = getattr(
                self.config.rc.simulation_configuration.execution_parameters,
                self.app_name,
                None,
            )
            self.sim_start_time = parameters.sim_start_time
            self.sim_stop_time = parameters.sim_stop_time
            self.start_time = parameters.start_time
            self.time_step = parameters.time_step
            self.time_scale_factor = parameters.time_scale_factor
            self.time_scale_updates = parameters.time_scale_updates
            self.freezes = parameters.freezes
            self.time_status_step = parameters.time_status_step
            self.time_status_init = parameters.time_status_init
            self.command_lead = parameters.command_lead
            self.required_apps = [
                app for app in parameters.required_apps if app != self.app_name
            ]
            self.init_retry_delay_s = parameters.init_retry_delay_s
            self.init_max_retry = parameters.init_max_retry
        else:
            logger.info(
                f"Collecting execution parameters from user input or default values."
            )
            self.sim_start_time = sim_start_time
            self.sim_stop_time = sim_stop_time
            self.start_time = start_time
            self.time_step = time_step
            self.time_scale_factor = time_scale_factor
            self.time_scale_updates = time_scale_updates
            self.freezes = freezes
            self.time_status_step = time_status_step
            self.time_status_init = time_status_init
            self.command_lead = command_lead
            self.required_apps = required_apps
            self.init_retry_delay_s = init_retry_delay_s
            self.init_max_retry = init_max_retry

        # Convert TimeScaleUpdateSchema objects to TimeScaleUpdate objects
        converted_updates = []
        for update_schema in self.time_scale_updates:
            converted_updates.append(
                TimeScaleUpdate(
                    time_scale_factor=update_schema.time_scale_factor,
                    sim_update_time=update_schema.sim_update_time,
                )
            )
        self.time_scale_updates = converted_updates

        # Convert FreezeSchema objects to Freeze objects
        converted_freezes = []
        for freeze_schema in self.freezes:
            converted_freezes.append(
                Freeze(
                    sim_freeze_time=freeze_schema.sim_freeze_time,
                    freeze_duration=freeze_schema.freeze_duration,
                )
            )
        self.freezes = converted_freezes

        # Set up tracking of required applications
        self.required_apps_status = dict(
            zip(self.required_apps, [False] * len(self.required_apps))
        )
        self.add_message_callback("*", "status.ready", self.on_app_ready_status)
        self.add_message_callback("*", "status.time", self.on_app_time_status)

        self._create_time_status_publisher(self.time_status_step, self.time_status_init)

        # Initialize with retry logic
        for i in range(self.init_max_retry):
            self.init(self.sim_start_time, self.sim_stop_time, self.required_apps)
            next_try = self.simulator.get_wallclock_time() + timedelta(
                seconds=self.init_retry_delay_s
            )
            while (
                not all([self.required_apps_status[app] for app in self.required_apps])
                and self.simulator.get_wallclock_time() < next_try
            ):
                time.sleep(0.001)

        # Configure start time if not provided
        if self.start_time is None:
            self.start_time = self.simulator.get_wallclock_time() + self.command_lead

        # Sleep until start time using heartbeat-safe approach
        sleep_seconds = max(
            0,
            (
                (self.start_time - self.simulator.get_wallclock_time())
                - self.command_lead
            )
            / timedelta(seconds=1),
        )

        # Use our heartbeat-safe sleep
        self._sleep_with_heartbeat(sleep_seconds)

        # Issue the start command
        self.start(
            self.sim_start_time,
            self.sim_stop_time,
            self.start_time,
            self.time_step,
            self.time_scale_factor,
            self.time_status_step,
            self.time_status_init,
        )

        # Wait for simulation to start executing
        while self.simulator.get_mode() != Mode.EXECUTING:
            time.sleep(0.001)

        # Combine and sort time scale updates and freezes by their scheduled times
        scheduled_events = []

        # Add time scale updates
        for update in self.time_scale_updates:
            scheduled_events.append(("update", update.sim_update_time, update))

        # Add freezes
        for freeze in self.freezes:
            scheduled_events.append(("freeze", freeze.sim_freeze_time, freeze))

        # Sort events by scheduled time
        scheduled_events.sort(key=lambda x: x[1])

        # # Track total freeze time to adjust final stop timing
        # self.total_freeze_time = timedelta(0)

        # Process all scheduled events in chronological order
        for event_type, event_time, event_obj in scheduled_events:
            event_wallclock_time = self.simulator.get_wallclock_time_at_simulation_time(
                event_time
            )

            # Sleep until event time using heartbeat-safe approach
            sleep_seconds = max(
                0,
                (
                    (event_wallclock_time - self.simulator.get_wallclock_time())
                    - self.command_lead
                )
                / timedelta(seconds=1),
            )

            # Use our heartbeat-safe sleep
            self._sleep_with_heartbeat(sleep_seconds)

            if event_type == "update":
                # Issue the update command
                self.update(event_obj.time_scale_factor, event_obj.sim_update_time)

                # Wait until update takes effect
                while (
                    self.simulator.get_time_scale_factor()
                    != event_obj.time_scale_factor
                ):
                    time.sleep(0.001)

            elif event_type == "freeze":
                if event_obj.is_timed:
                    # Timed freeze - will automatically resume after specified duration
                    self.freeze(event_obj.freeze_duration, event_obj.sim_freeze_time)
                    # Add the freeze duration to our total freeze time
                    self.total_freeze_time += event_obj.freeze_duration
                    self.resume()
                else:
                    # Indefinite freeze - requires manual resume
                    logger.warning(
                        f"Indefinite freeze scheduled at {event_obj.sim_freeze_time}. "
                        "Manual resume required to continue execution."
                    )
                    self.freeze(None, event_obj.sim_freeze_time)

        base_end_time = self.simulator.get_wallclock_time_at_simulation_time(
            self.simulator.get_end_time()
        )

        # Wait for stop time, checking for freeze time updates
        while True:
            with self._freeze_time_lock:
                current_end_time = base_end_time + self.total_freeze_time

            current_time = self.simulator.get_wallclock_time()
            time_until_stop = (
                current_end_time - current_time - self.command_lead
            ).total_seconds()

            if time_until_stop <= 0:
                break

            # Wait for either the timeout or a freeze time update
            timeout = min(30.0, time_until_stop)  # Check at least every 30 seconds
            if self._freeze_time_updated.wait(timeout):
                # Freeze time was updated, clear the event and recalculate
                self._freeze_time_updated.clear()
                continue

            # Timeout occurred, check if we should stop
            continue

        # Issue the stop command
        self.stop(self.sim_stop_time)

        # # Calculate end time accounting for freeze time
        # end_time = (
        #     self.simulator.get_wallclock_time_at_simulation_time(
        #         self.simulator.get_end_time()
        #     )
        #     + self.total_freeze_time
        # )

        # # Sleep until stop time using heartbeat-safe approach
        # sleep_seconds = max(
        #     0,
        #     ((end_time - self.simulator.get_wallclock_time()) - self.command_lead)
        #     / timedelta(seconds=1),
        # )

        # # Use our heartbeat-safe sleep
        # self._sleep_with_heartbeat(sleep_seconds)

        # # Issue the stop command
        # self.stop(self.sim_stop_time)

    def on_app_ready_status(self, ch, method, properties, body) -> None:
        """
        Callback to handle a message containing an application ready status.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # split the message topic into components (prefix/app_name/...)
            topic_parts = method.routing_key.split(".")
            message = body.decode("utf-8")
            # check if app_name is monitored in the ready_status dict
            if len(topic_parts) > 1 and topic_parts[1] in self.required_apps_status:
                # validate if message is a valid JSON
                try:
                    # update the ready status based on the payload value
                    self.required_apps_status[topic_parts[1]] = (
                        ReadyStatus.model_validate_json(message).properties.ready
                    )
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON format: {message}")
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
        except Exception as e:
            logger.error(
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def on_app_time_status(self, ch, method, properties, body) -> None:
        """
        Callback to handle a message containing an application time status.

        Args:
            ch (:obj:`pika.channel.Channel`): The channel object used to communicate with the RabbitMQ server.
            method (:obj:`pika.spec.Basic.Deliver`): Delivery-related information such as delivery tag, exchange, and routing key.
            properties (:obj:`pika.BasicProperties`): Message properties including content type, headers, and more.
            body (bytes): The actual message body sent, containing the message payload.
        """
        try:
            # split the message topic into components (prefix/app_name/...)
            topic_parts = method.routing_key.split(".")
            message = body.decode("utf-8")
            # validate if message is a valid JSON
            try:
                # parse the message payload properties
                props = TimeStatus.model_validate_json(message).properties
                wallclock_delta = self.simulator.get_wallclock_time() - props.time
                scenario_delta = self.simulator.get_time() - props.sim_time
                if len(topic_parts) > 1:
                    logger.info(
                        f"Application {topic_parts[1]} latency: {scenario_delta} (scenario), {wallclock_delta} (wallclock)"
                    )
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format: {message}")
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
        except Exception as e:
            logger.error(
                f"Exception (topic: {method.routing_key}, payload: {message}): {e}"
            )
            print(traceback.format_exc())

    def init(
        self,
        sim_start_time: datetime,
        sim_stop_time: datetime,
        required_apps: List[str] = [],
    ) -> None:
        """
        Publishes an initialize command to initialize a test run execution.

        Args:
            sim_start_time (:obj:`datetime`): Earliest possible scenario start time
            sim_stop_time (:obj:`datetime`): Latest possible scenario end time
            required_apps (list(str)): List of required apps
        """
        # publish init command message
        command = InitCommand.model_validate(
            {
                "taskingParameters": {
                    "simStartTime": sim_start_time,
                    "simStopTime": sim_stop_time,
                    "requiredApps": required_apps,
                }
            }
        )
        logger.info(
            f"Sending initialize command {command.model_dump_json(by_alias=True)}."
        )
        self.send_message(
            app_name=self.app_name,
            app_topics="init",
            payload=command.model_dump_json(by_alias=True),
        )
        # logger.info(f"Declared Queues: {self.declared_queues}")
        # logger.info(f"Declared Exchanges: {self.declared_exchanges}")

    def start(
        self,
        sim_start_time: datetime,
        sim_stop_time: datetime,
        start_time: datetime = None,
        time_step: timedelta = timedelta(seconds=1),
        time_scale_factor: float = 1.0,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
    ) -> None:
        """

        Command to start a test run execution by starting the simulator execution with all necessary parameters and publishing
        a start command, which can be received by the connected applications.

        Args:
            sim_start_time (:obj:`datetime`): Scenario time at which to start execution
            sim_stop_time (:obj:`datetime`): Scenario time at which to stop execution
            start_time (:obj:`datetime`): Wallclock time at which to start execution (default: now)
            time_step (:obj:`timedelta`): Scenario time step used in execution (default: 1 second)
            time_scale_factor (float): Scenario seconds per wallclock second (default: 1.0)
            time_status_step (:obj:`timedelta`): Scenario duration between time status messages
            time_status_init (:obj:`datetime`): Scenario time of first time status message
        """
        if start_time is None:
            start_time = self.simulator.get_wallclock_time()
        self.time_status_step = time_status_step
        self.time_status_init = time_status_init
        # publish a start command message
        command = StartCommand.model_validate(
            {
                "taskingParameters": {
                    "startTime": start_time,
                    "simStartTime": sim_start_time,
                    "simStopTime": sim_stop_time,
                    "timeScalingFactor": time_scale_factor,
                }
            }
        )
        logger.info(f"Sending start command {command.model_dump_json(by_alias=True)}.")
        self.send_message(
            app_name=self.app_name,
            app_topics="start",
            payload=command.model_dump_json(by_alias=True),
        )
        exec_thread = threading.Thread(
            target=self.simulator.execute,
            kwargs={
                "init_time": sim_start_time,
                "duration": sim_stop_time - sim_start_time,
                "time_step": time_step,
                "wallclock_epoch": start_time,
                "time_scale_factor": time_scale_factor,
            },
        )
        exec_thread.start()

    def stop(self, sim_stop_time: datetime) -> None:
        """
        Command to stop a test run execution by updating the execution end time and publishing a stop command.

        Args:
            sim_stop_time (:obj:`datetime`): Scenario time at which to stop execution.
        """
        # publish a stop command message
        command = StopCommand.model_validate(
            {"taskingParameters": {"simStopTime": sim_stop_time}}
        )
        logger.info(f"Sending stop command {command.model_dump_json(by_alias=True)}.")
        self.send_message(
            app_name=self.app_name,
            app_topics="stop",
            payload=command.model_dump_json(by_alias=True),
        )

        # Update the execution end time if simulator is in EXECUTING mode
        if self.simulator.get_mode() == Mode.EXECUTING:
            try:
                self.simulator.set_end_time(sim_stop_time)
            except RuntimeError as e:
                logger.warning(f"Could not set simulator end time: {e}")
        else:
            logger.debug(
                "Skipping setting simulator end time as simulator is not in EXECUTING mode"
            )

    def update(self, time_scale_factor: float, sim_update_time: datetime) -> None:
        """
        Command to update the time scaling factor for a test run execution by updating the execution time scale factor,
        and publishing an update command.

        Args:
            time_scale_factor (float): scenario seconds per wallclock second
            sim_update_time (:obj:`datetime`): scenario time at which to update
        """
        # publish an update command message
        command = UpdateCommand.model_validate(
            {
                "taskingParameters": {
                    "simUpdateTime": sim_update_time,
                    "timeScalingFactor": time_scale_factor,
                }
            }
        )
        logger.info(f"Sending update command {command.model_dump_json(by_alias=True)}.")
        self.send_message(
            app_name=self.app_name,
            app_topics="update",
            payload=command.model_dump_json(by_alias=True),
        )
        # update the execution time scale factor
        self.simulator.set_time_scale_factor(time_scale_factor, sim_update_time)

    def freeze(
        self, freeze_duration: timedelta = None, sim_freeze_time: datetime = None
    ) -> None:
        """
        Command to freeze a test run execution by updating the execution freeze duration and publishing a freeze command.

        Args:
            freeze_duration (:obj:`timedelta`, optional): Duration for which to freeze execution.
                                                        If None, creates an indefinite freeze.
            sim_freeze_time (:obj:`datetime`, optional): Scenario time at which to freeze execution.
                                                        If None, freezes immediately.
        """
        # publish a freeze command message
        command_params = {"simFreezeTime": sim_freeze_time}
        if freeze_duration is not None:
            command_params["freezeDuration"] = freeze_duration

        command = FreezeCommand.model_validate({"taskingParameters": command_params})

        freeze_type = (
            "indefinite" if freeze_duration is None else f"timed ({freeze_duration})"
        )
        logger.info(
            f"Sending {freeze_type} freeze command {command.model_dump_json(by_alias=True)}."
        )

        self.send_message(
            app_name=self.app_name,
            app_topics="freeze",
            payload=command.model_dump_json(by_alias=True),
        )

        # freeze simulation time
        self.simulator.pause()

        if freeze_duration is not None:
            # Timed freeze - automatically resume after duration
            time.sleep(freeze_duration.total_seconds())
        else:
            logger.info("Indefinite freeze active. Call resume() to continue.")
            while self.simulator.get_mode() not in [Mode.EXECUTING, Mode.RESUMING]:
                # Indefinite freeze - requires manual resume
                self._sleep_with_heartbeat(0.001)

    def resume(self) -> None:
        """
        Command to resume a test run execution by unpausing the simulator.
        """
        # resume the simulator execution
        command = ResumeCommand.model_validate(
            {
                "taskingParameters": {
                    "resumeTime": self.simulator.get_wallclock_time(),
                    "simResumeTime": self.simulator.get_time(),
                }
            }
        )
        logger.info(f"Sending resume command {command.model_dump_json(by_alias=True)}.")
        self.send_message(
            app_name=self.app_name,
            app_topics="resume",
            payload=command.model_dump_json(by_alias=True),
        )
        # resume simulation time
        self.simulator.resume()
