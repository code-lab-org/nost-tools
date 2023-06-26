from pydantic import BaseModel, Field, confloat
from datetime import datetime
from numpy import ndarray


class SatelliteStatus(BaseModel):
    # id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling.")
    geocentric_position: list = Field(
        ..., description="Position in inertial XYZ coordinates (m)"
    )
    latitude: float = Field(..., description="Satellite subpoint latitude (degrees)")
    longitude: float = Field(..., description="Satellite subpoint longitude (degrees)")
    altitude: float = Field(
        ..., description="Satellite altitude above surface of Earth (m)"
    )
    velocity: list = Field(
        ..., description="Velocity in intertial XYZ coordinates (m/s)"
    )
    time: datetime = Field(..., description="Time in satellite reference frame")
