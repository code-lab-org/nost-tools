# -*- coding: utf-8 -*-Fire
"""
Example script to specify object schemas for the EventSat test case.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


class EventState(str, Enum):
    undefined = "undefined"
    started = "started"
    finished = "finished"
    detected = "detected"
    reported = "reported"


class EventStarted(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    start: Optional[datetime] = Field(description="Time event started.")
    finish: Optional[datetime] = Field(description="Time event finished.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(
        description="Latitude (deg) of event location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field(
        description="Longitude (deg) of event location."
    )


class EventDetected(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    detected: datetime = Field(..., description="Time event detected.")
    detected_by: str = Field(..., description="Satellite name that detected the event.")


class EventReported(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    reported: datetime = Field(..., description="Time event reported.")
    reported_by: str = Field(
        ..., description="Satellite name that sent the event report."
    )
    reported_to: int = Field(
        ..., description="Station id that received the event report."
    )


class EventFinished(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")


class SatelliteStatus(BaseModel):
    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling.")
    latitude: confloat(ge=-90, le=90) = Field(
        ..., description="Latitude (deg) of satellite subpoint location."
    )
    longitude: confloat(ge=-180, le=180) = Field(
        ..., description="Longitude (deg) of satellite subpoint location."
    )
    altitude: float = Field(
        ..., description="Altitude (meters) of satellite above sea level"
    )
    radius: float = Field(..., description="Radius of nadir pointing cone of vision")
    commRange: bool = Field(
        False, description="Boolean for if satellite is in ground stations view"
    )
    time: datetime = Field(..., description="Time in satellite reference frame")


class GroundLocation(BaseModel):
    groundId: int = Field(..., description="Unique ground station identifier.")
    latitude: confloat(ge=-90, le=90) = Field(
        ..., description="Latitude (deg) of ground station."
    )
    longitude: confloat(ge=-180, le=180) = Field(
        ..., description="Longitude (deg) of ground station."
    )
    elevAngle: float = Field(
        ...,
        description="Minimum elevation angle (deg) for satellite-ground communications",
    )
    operational: bool = Field(
        True, description="True, if this ground station is operational."
    )
