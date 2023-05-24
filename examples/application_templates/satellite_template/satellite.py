from scipy.spatial.transform import Rotation as R
import numpy as np

from skyfield.api import load, wgs84, EarthSatellite
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from schemas import *


class Satellite(Entity):

    def __init__(self, app, id, name, ES=None, tle=None):
        super().__init__(name)
        self.app = app
        self.ts = load.timescale()
        
        if ES is not None:
            self.ES = ES
        if tle is not None:
            self.ES = EarthSatellite(tle[0], tle[1], name)

        self.id = id
        self.name = name
        self.satellites = []

        self.geocentric = self.next_geocentric = None
        self.geocentricPos = self.next_geocentricPos = None
        self.vel = self.next_vel = None
        self.geographicPos = self.next_geographicPos = None



    def initialize(self, init_time):

        super().initialize(init_time)
        self.geocentric = self.ES.at(self.ts.from_datetime(init_time))
        self.geocentricPos = self.geocentric.position.m
        self.vel = self.geocentric.velocity.m_per_s
        self.geographicPos = self.next_geographicPos = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]

    def tick(self, time_step):  # computes
        super().tick(time_step)
        self.next_geocentric = self.ES.at(
            self.ts.from_datetime(self.get_time() + time_step))
        self.next_geocentricPos = self.next_geocentric.position.m
        self.next_vel = self.next_geocentric.velocity.m_per_s
        self.next_geographicPos =         self.next_positions = [
            wgs84.subpoint(
                satellite.at(self.ts.from_datetime(self.get_time() + time_step))
            )
            for satellite in self.satellites
        ]


    def tock(self):
        self.geocentric = self.next_geocentric
        self.geocentricPos = self.next_geocentricPos
        self.vel = self.next_vel
        self.geographicPos = self.next_geographicPos

        super().tock()



# define a publisher to report satellite status
class StatusPublisher(WallclockTimeIntervalPublisher):

    def __init__(
        self, app, satellite, time_status_step=None, time_status_init=None
    ):
        super().__init__(app, time_status_step, time_status_init)
        self.satellite = satellite
        self.isInRange = False

    def publish_message(self):
        # if self.satellite.att==None:
        #     return
        next_time = self.satellite.ts.from_datetime(
            self.satellite.get_time() + 60 * self.time_status_step
        )
        satSpaceTime = self.satellite.ES.at(next_time)
        subpoint = wgs84.subpoint(satSpaceTime)


        self.app.send_message(
            "state",
            SatelliteStatus(
                id=self.satellite.id,
                name=self.satellite.name,
                geocentric_position=list(self.satellite.geocentricPos),
                geographic_position=list(self.satellite.geographicPos),
                velocity=list(self.satellite.vel),
                time=self.satellite.get_time(),
            ).json(),
        )
