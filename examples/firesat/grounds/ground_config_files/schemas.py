# -*- coding: utf-8 -*-
"""
*Schema are implemented using the pydantic library. The following schema define consistent message structures between this Constellation application and other observer applications:*

"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FireState(str, Enum):
    """ """

    undefined = "undefined"
    started = "started"
    detected = "detected"
    reported = "reported"


class FireStarted(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized message for fire ignition includes:

    """

    fireId: int = Field(..., description="Unique fire identifier.")
    start: Optional[datetime] = Field(description="Time fire started.")
    latitude: Optional[float] = Field(
        ge=-90, le=90, description="Latitude (deg) of fire location."
    )
    longitude: Optional[float] = Field(
        ge=-180, le=180, description="Longitude (deg) of fire location."
    )


class FireDetected(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized message for fire detection includes:

    """

    fireId: int = Field(..., description="Unique fire identifier.")
    detected: datetime = Field(..., description="Time fire detected.")
    detected_by: str = Field(..., description="Satellite name that detected the fire.")


class FireReported(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized message for fire reporting includes:

    """

    fireId: int = Field(..., description="Unique fire identifier.")
    reported: datetime = Field(..., description="Time fire reported.")
    reported_by: str = Field(
        ..., description="Satellite name that sent the fire report."
    )
    reported_to: int = Field(
        ..., description="Station id that received the fire report."
    )


class SatelliteStatus(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized satellite status message includes:

    """

    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling.")
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude (deg) of satellite subpoint location."
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude (deg) of satellite subpoint location.",
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

    Standardized message for ground station information includes:

    """

    groundId: int = Field(..., description="Unique ground station identifier.")
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude (deg) of ground station."
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude (deg) of ground station."
    )
    elevAngle: float = Field(
        ...,
        description="Minimum elevation angle (deg) for satellite-ground communications",
    )
    operational: bool = Field(
        True, description="True, if this ground station is operational."
    )
