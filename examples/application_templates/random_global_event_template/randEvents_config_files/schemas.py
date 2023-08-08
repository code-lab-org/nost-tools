# -*- coding: utf-8 -*-Fire
"""
Example script to specify object schemas for the EventSat test case.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime


class EventStarted(BaseModel):
    """
    *Standardized message indicating location, start-time, and isDay boolean for an event*
    """
    eventId: int = Field(..., description="Unique event identifier.")
    eventStart: Optional[datetime] = Field(description="Time event started.")
    latitude: float = Field(
        ..., ge=-90, le=90, description="Random event latitude (degrees)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Random event longitude (degrees)"
    )
    isDay: Optional[int] = Field()


class EventDayChange(BaseModel):
    """
    *Standardized message indicating an inversion of the isDay boolean switch*
    """
    eventId: int = Field(..., description="Unique event identifier.")
    isDay: int = Field(..., description="True if sunrise, false if sunset.")


class EventFinished(BaseModel):
    """
    *Standardized message indicating only the eventId which indicates the event has terminated and is no longer observable*
    """
    eventId: int = Field(..., description="Unique event identifier.")