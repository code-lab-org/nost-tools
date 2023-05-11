# -*- coding: utf-8 -*-
"""
Example script to specify object schemas for the FireSat test case.

@author: Paul T. Grogan <pgrogan@stevens.edu>
"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


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
        description="Minimum elevation angle (deg) for satellite-ground communications"
    )
