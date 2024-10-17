# -*- coding: utf-8 -*-
"""
    *This is an example of a common schema file that defines consistent message structures between applications.*

    Words Words Words.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


class FireState(str, Enum):
    """
    
    """
    undefined = "undefined"
    started = "started"
    detected = "detected"
    reported = "reported"


class FireStarted(BaseModel):
    """
    
    """
    fireId: int = Field(..., description="Unique fire identifier.")
    start: Optional[datetime] = Field(description="Time fire started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(
        description="Latitude (deg) of fire location."
    )
    longitude: Optional[confloat(ge=-180, le=180)] = Field(
        description="Longitude (deg) of fire location."
    )


class FireDetected(BaseModel):
    """
    
    """
    fireId: int = Field(..., description="Unique fire identifier.")
    detected: datetime = Field(..., description="Time fire detected.")
    detected_by: str = Field(..., description="Satellite name that detected the fire.")


class FireReported(BaseModel):
    """
    
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

    velocity: list[float] = Field(
        ..., description="Velocity of satellite in ECI frame"
    )
    state: bool = Field(
        ..., description="Boolean for if satellite is operational"
    )
    ecef: list[float] = Field(
        ..., description="ECEF position of satellite"
    )
    swath: float = Field(
        ..., description="Swath width of satellite"
    )
    # scanning: bool = Field(
    #     ..., description="Boolean for if satellite is scanning"
    # )
    snow_layer: str = Field(
        ..., description="Snow layer of satellite"
    )
    resolution_layer: str = Field(
        ..., description="Resolution layer of satellite"
    )
    gcom_layer: str = Field(
        ..., description="GCOM layer of satellite"
    )
    capella_layer: str = Field(
        ..., description="Capella layer of satellite"
    )
    top_left: list[float] = Field(
        ..., description="Top left corner of satellite"
    )
    top_right: list[float] = Field(
        ..., description="Top right corner of satellite"
    )
    bottom_left: list[float] = Field(
        ..., description="Bottom left corner of satellite"
    )
    bottom_right: list[float] = Field(
        ..., description="Bottom right corner of satellite"
    )


class GroundLocation(BaseModel):
    """
    
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
