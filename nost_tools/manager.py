"""
Provides a base manager that coordinates a distributed scenario execution.
"""

from datetime import datetime, timedelta
import logging
from paho.mqtt.client import Client, MQTTMessage
import threading
import time
import traceback
from typing import List

from .application import Application
from .schemas import (
    InitCommand,
    StartCommand,
    StopCommand,
    UpdateCommand,
    ReadyStatus,
    TimeStatus,
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

    def execute_test_plan(
        self,
        sim_start_time: datetime,
        sim_stop_time: datetime,
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
        self.required_apps_status = dict(
            zip(required_apps, [False] * len(required_apps))
        )
        self.add_message_callback("+", "status/ready", self.on_app_ready_status)
        self.add_message_callback("+", "status/time", self.on_app_time_status)

        self._create_time_status_publisher(time_status_step, time_status_init)
        for i in range(init_max_retry):
            # issue the init command
            self.init(sim_start_time, sim_stop_time, required_apps)
            next_try = self.simulator.get_wallclock_time() + timedelta(
                seconds=init_retry_delay_s
            )
            # wait until all required apps are ready
            while (
                not all([self.required_apps_status[app] for app in required_apps])
                and self.simulator.get_wallclock_time() < next_try
            ):
                time.sleep(0.001)
        self.remove_message_callback("+", "status/ready")
        # configure start time
        if start_time is None:
            start_time = self.simulator.get_wallclock_time() + command_lead
        # sleep until the start command needs to be issued
        time.sleep(
            max(
                0,
                ((start_time - self.simulator.get_wallclock_time()) - command_lead)
                / timedelta(seconds=1),
            )
        )
        # issue the start command
        self.start(
            sim_start_time,
            sim_stop_time,
            start_time,
            time_step,
            time_scale_factor,
            time_status_step,
            time_status_init,
        )
        # wait for simulation to start executing
        while self.simulator.get_mode() != Mode.EXECUTING:
            time.sleep(0.001)
        for update in time_scale_updates:
            update_time = self.simulator.get_wallclock_time_at_simulation_time(
                update.sim_update_time
            )
            # sleep until the update command needs to be issued
            time.sleep(
                max(
                    0,
                    ((update_time - self.simulator.get_wallclock_time()) - command_lead)
                    / timedelta(seconds=1),
                )
            )
            # issue the update command
            self.update(update.time_scale_factor, update.sim_update_time)
            # wait until the update command takes effect
            while self.simulator.get_time_scale_factor() != update.time_scale_factor:
                time.sleep(command_lead / timedelta(seconds=1) / 100)
        end_time = self.simulator.get_wallclock_time_at_simulation_time(
            self.simulator.get_end_time()
        )
        # sleep until the stop command should be issued
        time.sleep(
            max(
                0,
                ((end_time - self.simulator.get_wallclock_time()) - command_lead)
                / timedelta(seconds=1),
            )
        )
        # issue the stop command
        self.stop(sim_stop_time)

    def on_app_ready_status(
        self, client: Client, userdata: object, message: MQTTMessage
    ) -> None:
        """
        Callback to handle a message containing an application ready status.
        """
        try:
            # split the message topic into components (prefix/app_name/...)
            topic_parts = message.topic.split("/")
            # check if app_name is monitored in the ready_status dict
            if len(topic_parts) > 1 and topic_parts[1] in self.required_apps_status:
                # update the ready status based on the payload value
                self.required_apps_status[topic_parts[1]] = ReadyStatus.parse_raw(
                    message.payload
                ).properties.ready
        except Exception as e:
            logger.error(
                f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
            )
            print(traceback.format_exc())

    def on_app_time_status(
        self, client: Client, userdata: object, message: MQTTMessage
    ) -> None:
        """
        Callback to handle a message containing an application time status.
        """
        try:
            # split the message topic into components (prefix/app_name/...)
            topic_parts = message.topic.split("/")
            # parse the message payload properties
            props = TimeStatus.parse_raw(message.payload).properties
            wallclock_delta = self.simulator.get_wallclock_time() - props.time
            scenario_delta = self.simulator.get_time() - props.sim_time
            if len(topic_parts) > 1:
                logger.info(
                    f"Application {topic_parts[1]} latency: {scenario_delta} (scenario), {wallclock_delta} (wallclock)"
                )
        except Exception as e:
            logger.error(
                f"Exception (topic: {message.topic}, payload: {message.payload}): {e}"
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
        command = InitCommand.parse_obj(
            {
                "taskingParameters": {
                    "simStartTime": sim_start_time,
                    "simStopTime": sim_stop_time,
                    "requiredApps": required_apps,
                }
            }
        )
        logger.info(f"Sending initialize command {command.json(by_alias=True)}.")
        self.client.publish(
            f"{self.prefix}/{self.app_name}/init", command.json(by_alias=True)
        )

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
        command = StartCommand.parse_obj(
            {
                "taskingParameters": {
                    "startTime": start_time,
                    "simStartTime": sim_start_time,
                    "simStopTime": sim_stop_time,
                    "timeScalingFactor": time_scale_factor,
                }
            }
        )
        logger.info(f"Sending start command {command.json(by_alias=True)}.")
        self.client.publish(
            f"{self.prefix}/{self.app_name}/start", command.json(by_alias=True)
        )
        # start execution in a background thread
        threading.Thread(
            target=self.simulator.execute,
            kwargs={
                "init_time": sim_start_time,
                "duration": sim_stop_time - sim_start_time,
                "time_step": time_step,
                "wallclock_epoch": start_time,
                "time_scale_factor": time_scale_factor,
            },
        ).start()

    def stop(self, sim_stop_time: datetime) -> None:
        """
        Command to stop a test run execution by updating the execution end time and publishing a stop command.

        Args:
            sim_stop_time (:obj:`datetime`): Scenario time at which to stop execution.
        """
        # publish a stop command message
        command = StopCommand.parse_obj(
            {"taskingParameters": {"simStopTime": sim_stop_time}}
        )
        logger.info(f"Sending stop command {command.json(by_alias=True)}.")
        self.client.publish(
            f"{self.prefix}/{self.app_name}/stop", command.json(by_alias=True)
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
        command = UpdateCommand.parse_obj(
            {
                "taskingParameters": {
                    "simUpdateTime": sim_update_time,
                    "timeScalingFactor": time_scale_factor,
                }
            }
        )
        logger.info(f"Sending update command {command.json(by_alias=True)}.")
        self.client.publish(
            f"{self.prefix}/{self.app_name}/update", command.json(by_alias=True)
        )
        # update the execution time scale factor
        self.simulator.set_time_scale_factor(time_scale_factor, sim_update_time)
