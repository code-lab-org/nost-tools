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
from .schemas import (
    InitCommand,
    ReadyStatus,
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

    def __init__(self):
        """
        Initializes a new manager.
        """
        # call super class constructor
        super().__init__("manager")
        self.required_apps_status = {}

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
            durable=False,
            auto_delete=True,
        )

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

    def _execute_test_plan_impl(
        self,
        sim_start_time: datetime = None,
        sim_stop_time: datetime = None,
        start_time: datetime = None,
        time_step: timedelta = timedelta(seconds=1),
        time_scale_factor: float = 1.0,
        time_scale_updates: List[TimeScaleUpdate] = [],
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
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time of first time status message
            command_lead (:obj:`timedelta`): wallclock lead time between command and action (default: 0 seconds)
            required_apps (list(str)): list of application names required to continue with the execution
            init_retry_delay_s (float): number of seconds to wait between initialization commands while waiting for required applications
            init_max_retry (int): number of initialization commands while waiting for required applications before continuing to execution
        """
        # Initialize parameters from arguments or config
        if sim_start_time is not None and sim_stop_time is not None:
            self.sim_start_time = sim_start_time
            self.sim_stop_time = sim_stop_time
            self.start_time = start_time
            self.time_step = time_step
            self.time_scale_factor = time_scale_factor
            self.time_scale_updates = time_scale_updates
            self.time_status_step = time_status_step
            self.time_status_init = time_status_init
            self.command_lead = command_lead
            self.required_apps = required_apps
            self.init_retry_delay_s = init_retry_delay_s
            self.init_max_retry = init_max_retry
        else:
            if self.config.rc:
                logger.info("Retrieving execution parameters from YAML file.")
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
                self.time_status_step = parameters.time_status_step
                self.time_status_init = parameters.time_status_init
                self.command_lead = parameters.command_lead
                self.required_apps = [
                    app for app in parameters.required_apps if app != self.app_name
                ]
                self.init_retry_delay_s = parameters.init_retry_delay_s
                self.init_max_retry = parameters.init_max_retry
            else:
                raise ValueError(
                    "No configuration runtime. Please provide simulation start and stop times."
                )

        self.establish_exchange()

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

        # Process time scale updates
        for update in self.time_scale_updates:
            update_time = self.simulator.get_wallclock_time_at_simulation_time(
                update.sim_update_time
            )
            # Sleep until update time using heartbeat-safe approach
            sleep_seconds = max(
                0,
                (
                    (update_time - self.simulator.get_wallclock_time())
                    - self.command_lead
                )
                / timedelta(seconds=1),
            )

            # Use our heartbeat-safe sleep
            self._sleep_with_heartbeat(sleep_seconds)

            # Issue the update command
            self.update(update.time_scale_factor, update.sim_update_time)

            # Wait until update takes effect
            while self.simulator.get_time_scale_factor() != update.time_scale_factor:
                time.sleep(0.001)

        end_time = self.simulator.get_wallclock_time_at_simulation_time(
            self.simulator.get_end_time()
        )

        # Sleep until stop time using heartbeat-safe approach
        sleep_seconds = max(
            0,
            ((end_time - self.simulator.get_wallclock_time()) - self.command_lead)
            / timedelta(seconds=1),
        )

        # Use our heartbeat-safe sleep
        self._sleep_with_heartbeat(sleep_seconds)

        # Issue the stop command
        self.stop(self.sim_stop_time)

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
        # update the execution end time
        self.simulator.set_end_time(sim_stop_time)

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
