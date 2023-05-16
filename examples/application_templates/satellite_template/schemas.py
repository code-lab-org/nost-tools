from pydantic import BaseModel, Field, confloat
from datetime import datetime
from numpy import ndarray


class SatelliteStatus(BaseModel):
    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling.")
    geocentric_position: list = Field(
        ..., description="Position in inertial XYZ coordinates"
    )
    # geographical_position: list = Field(..., description="Position in geographical latitude-longitude-altitude")
    velocity: list = Field(..., description="Velocity in intertial XYZ coordinates")
    time: datetime = Field(..., description="Time in satellite reference frame")
