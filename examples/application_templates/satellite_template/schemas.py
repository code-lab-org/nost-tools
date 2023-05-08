from pydantic import BaseModel, Field, confloat
from datetime import datetime
from numpy import ndarray


class SatelliteStatus(BaseModel):
    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling.")
    position: list = Field(...,
                           description="Position in intertial XYZ coordinates")
    velocity: list = Field(...,
                           description="Velocity in intertial XYZ coordinates")
    radius: float = Field(...,
                          description="Radius of nadir pointing cone of vision")
    commRange: bool = Field(
        False, description="Boolean for if satellite is in ground stations view"
    )
    time: datetime = Field(...,
                           description="Time in satellite reference frame")
