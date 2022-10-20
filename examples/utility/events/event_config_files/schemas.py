# -*- coding: utf-8 -*-
"""
    *Common script between applications for standardizing object schemas for the FireSat+ test suite*
    
    Standardized schemas for messages are useful to ensure published message content matches the subscribing applications' expected information and data formats.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


class EventState(str, Enum):
    """
    *Enumeration used to classify the current state of the event:*

    .. literalinclude:: /../../eventsat/events/event_config_files/schemas.py
        :lines: 15,24-27

    """

    undefined = "undefined"
    started = "started"
    detected = "detected"
    reported = "reported"
    finished = "finished"


class EventStarted(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*
    
    Standardized message for event ignition includes eventId (*int*), ignition start (:obj:`datetime`), and latitude-longitude location (:obj:`GeographicPosition`)

    .. literalinclude:: /../../eventsat/events/event_config_files/schemas.py
        :lines: 30,41-48

    """

    eventId: int = Field(..., description="Unique event identifier.")
    start: Optional[datetime] = Field(description="Time event started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(
        description="Latitude (deg) of event location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field(
        description="Longitude (deg) of event location."
    )


class EventDetected(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*
    
    Standardized message for event detection includes eventId (*int*), time of detection (:obj:`datetime`), and name (*str*) of detecting satellite

    .. literalinclude:: /../../eventsat/events/event_config_files/schemas.py
        :lines: 51,62-64

    """

    eventId: int = Field(..., description="Unique event identifier.")
    detected: datetime = Field(..., description="Time event detected.")
    detected_by: str = Field(..., description="Satellite name that detected the event.")


class EventReported(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*
    
    Standardized message for event report includes eventId (*int*), time of report (:obj:`datetime`), name (*str*) of reporting satellite, and groundId (*int*) of ground station receiving report

    .. literalinclude:: /../../eventsat/events/event_config_files/schemas.py
        :lines: 67,78-85

    """

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
    finish: Optional[datetime] = Field(description="Time event started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(
        description="Latitude (deg) of event location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field(
        description="Longitude (deg) of event location."
    )


class SatelliteStatus(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*
    
    Standardized message for satellite position publisher includes satellite id (*int*), name (*str*), latitude-longitude-altitude location (:obj:`GeographicPosition`), sensor view radius (*float*), indication of whether comms in range of ground station (*bool*), and current scenario time (:obj:`datetime`)

    .. literalinclude:: /../../eventsat/events/event_config_files/schemas.py
        :lines: 88,99-114

    """

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
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*
    
    Standardized message for ground station information includes groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min elevation angle constraint (*float*), and operational status (*bool*)

    .. literalinclude:: /../../eventsat/events/event_config_files/schemas.py
        :lines: 117,128-141

    """

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
