# -*- coding: utf-8 -*-
"""
    *Common script between applications for standardizing object schemas for the FireSat+ test suite*

    Standardized schemas for messages are useful to ensure published message content matches the subscribing applications' expected information and data formats.

"""

from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime
from enum import Enum


class FireState(str, Enum):
    """
    *Enumeration used to classify the current state of the fire:*

    .. literalinclude:: /../../examples/firesat/fires/fire_config_files/schemas.py
        :lines: 15,24-27

    """
    undefined = "undefined"
    started = "started"
    detected = "detected"
    reported = "reported"


class FireStarted(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized message for fire ignition includes fireId (*int*), ignition start (:obj:`datetime`), and latitude-longitude location (:obj:`GeographicPosition`)

    .. literalinclude:: /../../examples/firesat/fires/fire_config_files/schemas.py
        :lines: 30,41-44

    """

    fireId: int = Field(..., description="Unique fire identifier.")
    start: Optional[datetime] = Field(description="Time fire started.")
    latitude: Optional[confloat(ge=-90, le=90)] = Field(description="Latitude (deg) of fire location.")
    longitude: Optional[confloat(ge=-180, le=180)] = Field(description="Longitude (deg) of fire location.")


class FireDetected(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized message for fire detection includes fireId (*int*), time of detection (:obj:`datetime`), and name (*str*) of detecting satellite

    .. literalinclude:: /../../examples/firesat/fires/fire_config_files/schemas.py
        :lines: 47,58-60

    """

    fireId: int = Field(..., description="Unique fire identifier.")
    detected: datetime = Field(..., description="Time fire detected.")
    detected_by: str = Field(..., description="Satellite name that detected the fire.")


class FireReported(BaseModel):
    """
    *Message schema object class with properties inherited from the pydantic library's BaseModel*

    Standardized message for fire report includes fireId (*int*), time of report (:obj:`datetime`), name (*str*) of reporting satellite, and groundId (*int*) of ground station receiving report

    .. literalinclude:: /../../examples/firesat/fires/fire_config_files/schemas.py
        :lines: 63,74-77

    """

    fireId: int = Field(..., description="Unique fire identifier.")
    reported: datetime = Field(..., description="Time fire reported.")
    reported_by: str = Field(..., description="Satellite name that sent the fire report.")
    reported_to: int = Field(..., description="Station id that received the fire report.")
