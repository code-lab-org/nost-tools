from pydantic import BaseModel, Field, confloat
from datetime import datetime
from numpy import ndarray


class SatelliteStatus(BaseModel):
    id: int = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name for labeling.")
    position: list = Field(..., description="Geocentric position")
    velocity: list = Field(..., description="Geocentric velocity")
    latitude: float = Field(..., description="Satellite latitude")
    longitude: float = Field(..., description="Satellite longitude")
    attitude: list = Field(..., description="Attitude quaternion")
    angular_velocity: list = Field(..., description="Angular velocity in body frame")
    target_quaternion: list = Field(..., description="Desired attitude quaternion")
    radius: float = Field(..., description="Radius of nadir pointing cone of vision")
    commRange: bool = Field(
        False, description="Boolean for if satellite is in ground stations view"
    )
    time: datetime = Field(..., description="Time in satellite reference frame")


class observation_success(BaseModel):
    targetId: int = Field(..., description="Unique target identifier.")
    detected: datetime = Field(..., description="Time target observed.")
    roll_angle_error: float = Field(
        ..., description="Difference between desired and actual roll angle (deg)."
    )
