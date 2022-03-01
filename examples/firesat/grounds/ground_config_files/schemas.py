# -*- coding: utf-8 -*-
"""
Example script to specify object schemas for the FireSat test case.

@author: Paul T. Grogan <pgrogan@stevens.edu>
"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


class FireState(str, Enum):
    undefined = "undefined"
    started = "started"
    detected = "detected"
    reported = "reported"


class FireStarted(BaseModel):
    fireId: int = Field(..., description="Unique fire identifier.")
    start: Optional[datetime] = Field(description="Time fire started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(
        description="Latitude (deg) of fire location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field(
        description="Longitude (deg) of fire location."
    )


class FireDetected(BaseModel):
    fireId: int = Field(..., description="Unique fire identifier.")
    detected: datetime = Field(..., description="Time fire detected.")
    detected_by: str = Field(..., description="Satellite name that detected the fire.")


class FireReported(BaseModel):
    fireId: int = Field(..., description="Unique fire identifier.")
    reported: datetime = Field(..., description="Time fire reported.")
    reported_by: str = Field(
        ..., description="Satellite name that sent the fire report."
    )
    reported_to: int = Field(
        ..., description="Station id that received the fire report."
    )


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
