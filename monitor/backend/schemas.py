from datetime import datetime, timedelta
from typing import List, Optional

from fastapi_utils.api_model import APIModel
from nost_tools import manager
from pydantic import Field

class InitRequest(APIModel):
    """
    Request for a manager `init` command to initialize a scenario execution.
    """
    sim_start_time: datetime = Field(
        ...,
        description="Earliest possible scenario start time."
    )
    sim_stop_time: datetime = Field(
        ...,
        description="Latest possible scenario end time."
    )
    required_apps: Optional[List[str]] = Field(
        [],
        description="List of application names required to publish a `ready` message before starting the scenario execution."
    )

class StartRequest(APIModel):
    """
    Request for a manager `start` command to start a new scenario execution.
    """
    sim_start_time: datetime = Field(
        ...,
        description="Scenario start time."
    )
    sim_stop_time: datetime = Field(
        ...,
        description="Scenario end time."
    )
    start_time: Optional[datetime] = Field(
        None,
        description="Wallclock start time."
    )
    time_step: timedelta = Field(
        timedelta(seconds=1),
        description="Scenario time interval between state updates."
    )
    time_scale_factor: Optional[float] = Field(
        1.0,
        description="Number of scenario seconds per wallclock second (greater than 1 is faster than real-time)."
    )
    time_status_step: Optional[timedelta] = Field(
        None,
        description="Scenario time interval between time status (heartbeat) messages."
    )
    time_status_init: Optional[datetime] = Field(
        None,
        description="Scenario time of the first time status (heartbeat) message."
    )

class StopRequest(APIModel):
    """
    Request for a manager `stop` command to schedule the end of a scenario execution.
    """
    sim_stop_time: datetime = Field(
        ...,
        description="Scenario end time."
    )

class UpdateRequest(APIModel):
    """
    Request for a manager `update` command to change the time scale factor for a scenario execution.
    """
    time_scale_factor: float = Field(
        ...,
        description="Number of scenario seconds per wallclock second (greater than 1 is faster than real-time)."
    )
    sim_update_time: datetime = Field(
        ...,
        description="Scenario update time."
    )

    def to_manager_format(self) -> manager.TimeScaleUpdate:
        """
        Transforms this time scale update to the NOS-T manager format.

        Returns:
            `nost_tools.manager.TimeScaleUpdate`: the formatted time scale update
        """
        return manager.TimeScaleUpdate(
            self.time_scale_factor, 
            self.sim_update_time
        )

class ExecuteRequest(InitRequest, StartRequest):
    """
    Request for the manager to execute a new end-to-end scenario execution.
    """
    time_scale_updates: Optional[List[UpdateRequest]] = Field(
        [],
        description="List of time scale updates to process during the execution."
    )
    command_lead: Optional[timedelta] = Field(
        timedelta(seconds=0),
        description="Wallclock time interval before command messages are published."
    )
    init_retry_delay_s: Optional[int] = Field(
        5,
        description="Number of wallclock seconds to wait for required applications to publish a `ready` message before re-sending an `init` command."
    )
    init_max_retry: Optional[int] = Field(
        5,
        description="Number of `init` commands to re-try for required applications before exiting."
    )
