from datetime import datetime, timedelta
from typing import List

from nost_tools import manager
from pydantic import BaseModel

class InitRequest(BaseModel):
    sim_start_time: datetime
    sim_stop_time: datetime
    required_apps: List[str] = []

class StartRequest(BaseModel):
    sim_start_time: datetime
    sim_stop_time: datetime
    start_time: datetime = None
    time_step: timedelta = timedelta(seconds=1)
    time_scale_factor: float = 1.0
    time_status_step: timedelta = None
    time_status_init: datetime = None

class StopRequest(BaseModel):
    sim_stop_time: datetime

class UpdateRequest(BaseModel):
    time_scale_factor: float
    sim_update_time: datetime

class TimeScaleUpdate(BaseModel):
    time_scale_factor: float
    sim_update_time: datetime

    def to_manager_format(self):
        return manager.TimeScaleUpdate(
            self.time_scale_factor, 
            self.sim_update_time
        )

class ExecuteRequest(BaseModel):
    sim_start_time: datetime
    sim_stop_time: datetime
    start_time: datetime = None
    time_step: timedelta = timedelta(seconds=1)
    time_scale_factor: float = 1.0
    time_scale_updates: List[TimeScaleUpdate] = []
    time_status_step: timedelta = None
    time_status_init: datetime = None
    command_lead: timedelta = timedelta(seconds=0)
    required_apps: List[str] = []
    init_retry_delay_s: int = 5
    init_max_retry: int = 5
