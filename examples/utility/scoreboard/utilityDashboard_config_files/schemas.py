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

    
class UtilityPub(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field( # type:ignore 
        description="Latitude (deg) of event location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field( # type:ignore
        description="Longitude (deg) of event location."
    )
    time: datetime = Field(..., description="Time input to u(t) function")
    isDay: bool = Field(..., description="True = Day, False = Night")
    utility: float = Field(..., description="Normalized science utility that is output of u(t)")
    isReal: bool = Field(..., description="True = Real Event Utility, False = Predicted Event Utility") 


class EventStarted(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    eventStart: Optional[datetime] = Field(description="Time event started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field( # type:ignore 
        description="Latitude (deg) of event location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field( # type:ignore
        description="Longitude (deg) of event location."
    )
    isDay: Optional[int] = Field()


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


class EventDayChange(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    isDay: int = Field(..., description="True if sunrise, false if sunset.")


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
