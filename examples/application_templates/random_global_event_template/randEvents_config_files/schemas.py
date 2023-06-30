# -*- coding: utf-8 -*-Fire
"""
Example script to specify object schemas for the EventSat test case.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime


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


class EventDayChange(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")
    isDay: int = Field(..., description="True if sunrise, false if sunset.")


class EventFinished(BaseModel):
    eventId: int = Field(..., description="Unique event identifier.")