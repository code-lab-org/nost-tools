# -*- coding: utf-8 -*-
"""
Example script to specify object schemas for the AWS Downlink test case.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime, timedelta


class GroundLocation(BaseModel):
    groundId: int = Field(..., description="Unique ground station identifier")
    latitude: confloat(ge=-90, le=90) = Field(
        ..., description="Latitude (deg) of ground station"
    )
    longitude: confloat(ge=-180, le=180) = Field(
        ..., description="Longitude (deg) of ground station"
    )
    elevAngle: float = Field(
        ..., description="Minimum elevation angle (deg) for satellite-ground communications",
    )
    operational: bool = Field(
        True, description="True, if this ground station is operational"
    )
    downlinkRate: float = Field(
        ..., description="Downlink rate for this ground station in Megabytes per second"
    )
    costPerSecond: float = Field(
        ..., description="Cost in $ per second for downlinks"
    )
    costMode: str = Field(
        "discrete", description="Could be a boolean, options are discrete or fixed, default to discrete"    
    )
    
class OutageReport(BaseModel):
    groundId: int = Field(..., description="Unique ground station identifier experiencing outage")
    outageStart: datetime = Field(
        ..., description="Initial time of outage report"
    )
    outageDuration: timedelta = Field(
        ..., description="Duration of the reported outage"
    )
    outageEnd: datetime = Field(
        ..., description="outageStart + outageDuration"
    )
    
class OutageRestore(BaseModel):
    groundId: int = Field(..., description="Unique ground station identifier")
    outageEnd: datetime = Field(
        ..., description = "outageStart + outageDuration"
    )