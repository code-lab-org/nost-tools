from pydantic import BaseModel, Field, confloat
from datetime import datetime
from typing import Optional, List

from .simulator import Mode


class InitTaskingParameters(BaseModel):
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
    tasking_parameters: InitTaskingParameters = Field(
        ...,
        description="Tasking parameters for the initialize command.",
        alias="taskingParameters",
    )


class StartTaskingParameters(BaseModel):
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
    time_scaling_factor: confloat(gt=0) = Field(
        1.0,
        description="Scenario seconds per wallclock second.",
        alias="timeScalingFactor",
    )


class StartCommand(BaseModel):
    tasking_parameters: StartTaskingParameters = Field(
        ...,
        description="Tasking parameters for the start command.",
        alias="taskingParameters",
    )


class StopTaskingParameters(BaseModel):
    sim_stop_time: datetime = Field(
        ...,
        description="Scenario time at which to stop execution.",
        alias="simStopTime",
    )


class StopCommand(BaseModel):
    tasking_parameters: StopTaskingParameters = Field(
        ...,
        description="Tasking parameters for the stop command.",
        alias="taskingParameters",
    )


class UpdateTaskingParameters(BaseModel):
    time_scaling_factor: confloat(gt=0) = Field(
        ...,
        description="Time scaling factor (scenario seconds per wallclock second).",
        alias="timeScalingFactor",
    )
    sim_update_time: datetime = Field(
        ...,
        description="Scenario time at which to update the time scaling factor.",
        alias="simUpdateTime",
    )


class UpdateCommand(BaseModel):
    tasking_parameters: UpdateTaskingParameters = Field(
        ...,
        description="Tasking parameters for the stop command.",
        alias="taskingParameters",
    )


class TimeStatusProperties(BaseModel):
    sim_time: datetime = Field(
        ..., description="Current scenario time.", alias="simTime"
    )
    time: datetime = Field(..., description="Current wallclock time.")


class TimeStatus(BaseModel):
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
    mode: Mode = Field(..., description="Current execution mode.")


class ModeStatus(BaseModel):
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
    ready: bool = Field(True, description="True, if this application is ready.")


class ReadyStatus(BaseModel):
    name: str = Field(
        ..., description="Name of the application providing a ready status."
    )
    description: Optional[str] = Field(
        None, description="Description of the application providing a ready status."
    )
    properties: ReadyStatusProperties = Field(
        ..., description="Properties for the ready status."
    )
