# -*- coding: utf-8 -*-
"""
Example script to specify object schemas for the flood imaging test case.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


class FloodState(str, Enum):
    undefined = "undefined" #?
    started = "started"
    imaged = "imaged"
    downlinked= "downlinked"


class FloodStarted(BaseModel):
    floodId: int = Field(..., description="Unique flood identifier.")
    startTime: Optional[datetime] = Field(description="Time flood started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(
        description="Latitude (deg) of flood location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field(
        description="Longitude (deg) of flood location."
    )
    

class FloodImaged(BaseModel):
    floodId: int = Field(..., description="Unique flood identifier.")
    imaged: datetime = Field(..., description="Time flood imaged.")
    imagedBy: str = Field(..., description="Satellite name that imaged the flood.")


class FloodDownlinked(BaseModel):
    floodId: int = Field(..., description="Unique flood identifier.")
    downlinked: datetime = Field(..., description="Time flood reported.")
    downlinkedBy: str = Field(
        ..., description="Satellite name that sent the flood image."
    )
    downlinkedTo: int = Field(
        ..., description="Station id that received the flood image."
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

