# -*- coding: utf-8 -*-
"""
Example script to specify object schemas for the AWS Downlink test case.
"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime, timedelta


class SatelliteReady(BaseModel):
    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling")
    ssr_capacity: float = Field(
        ..., description="Capacity of onboard Solid State Recorder in Gigabytes"
    )
    
    
class SatelliteAllReady(BaseModel):
    ready: str = Field(
        "allReady", description="Indicates completion of SatelliteReady messages"
    )
    

class SatelliteStatus(BaseModel):
    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling")
    latitude: confloat(ge=-90, le=90) = Field(
        ..., description="Latitude (deg) of satellite subpoint location"
    )
    longitude: confloat(ge=-180, le=180) = Field(
        ..., description="Longitude (deg) of satellite subpoint location"
    )
    altitude: float = Field(
        ..., description="Altitude (meters) of satellite above sea level"
    )
    capacity_used: float = Field(
        ..., 
        description="GB of solid state recorder capacity used"
    )
    commRange: bool = Field(
        False, description="Boolean for if satellite is in ground stations view"
    )
    groundId: Optional[int] = Field(
        ..., description="Ground Station id in view (None if not in view)"
    )
    totalLinkCount: Optional[int] = Field(
        ..., description="Running count of downlink opportunity per satellite"    
    )
    cumulativeCostBySat: float = Field(
        ..., description="Cumulative cost of downlinks and/or fixed cost contracts per satellite"    
    )
    time: datetime = Field(
        ..., description="Time in satellite reference frame"
    )


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
    
class LinkStart(BaseModel):
    groundId: int = Field(..., description="Unique ground station identifier")
    satId: int = Field(..., description="Unique satellite identifier that performed the downlink")
    satName: str = Field(..., description="Name of satellite that performed the downlink")
    linkId: int = Field(
        ..., description="Unique downlink counter for the specific spacecraft that downlinked"
    )
    start: datetime = Field(
        ..., description="Start time in ground network reference frame"
    )
    data: float = Field(
        ..., description="Current amount of data on-board the satellite that needs to be offloaded"
    )
    
class LinkCharge(BaseModel):
    groundId: int = Field(..., description="Unique ground station identifier")
    satId: int = Field(..., description="Unique satellite identifier that performed the downlink")
    satName: str = Field(..., description="Name of satellite that performed the downlink")
    linkId: int = Field(
        ..., description="Unique downlink counter for the specific spacecraft that downlinked"
    )
    end: datetime = Field(
        ...,
        description="Time stamp for end of downlink when charge is sent"
    )
    duration: float = Field(
        ..., description="Time duration of satellite in view for this downlink (s)"
    )
    dataOffload: float = Field(
        ..., description="Amount of data offloaded based on linear downlink rates unique to each ground station (GB)"
    )
    downlinkCost: float = Field(
        ..., description="Cost of data downlink based on per-second cost rates unique to each ground station"
    )
    cumulativeCostBySat: float = Field(
        ..., description="Dictionary of running totals for downlink costs per satellite"
    )
    cumulativeCosts: float = Field(
        ..., description="Running total of ALL downlink costs for the entirety of the Test Case"
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