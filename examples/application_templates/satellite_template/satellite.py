import numpy as np

from skyfield.api import load, wgs84, EarthSatellite
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from satellite_config_files.schemas import SatelliteStatus
from satellite_config_files.config import PARAMETERS


class Satellite(Entity):
    def __init__(self, app, name, ES=None, tle=None):
        super().__init__(name)
        self.app = app
        self.ts = load.timescale()

        if ES is not None:
            self.ES = ES
        if tle is not None:
            self.ES = EarthSatellite(tle[0], tle[1], name)

        self.name = name
        self.geocentric = self.next_geocentric = None
        self.geocentricPos = self.next_geocentricPos = None
        self.geographicPos = self.next_geographicPos = None
        self.vel = self.next_vel = None

    def initialize(self, init_time):
        super().initialize(init_time)
        self.geocentric = self.ES.at(self.ts.from_datetime(init_time))
        self.geocentricPos = self.geocentric.position.m
        self.geographicPos = wgs84.geographic_position_of(self.geocentric)
        self.vel = self.geocentric.velocity.m_per_s

    def tick(self, time_step):
        super().tick(time_step)
        self.next_geocentric = self.ES.at(
            self.ts.from_datetime(self.get_time() + time_step)
        )
        self.next_geocentricPos = self.next_geocentric.position.m
        self.next_geographicPos = wgs84.geographic_position_of(self.next_geocentric)
        self.next_vel = self.next_geocentric.velocity.m_per_s

    def tock(self):
        self.geocentric = self.next_geocentric
        self.geocentricPos = self.next_geocentricPos
        self.geographicPos = self.next_geographicPos
        self.vel = self.next_vel
        super().tock()


# define a publisher to report ES status
class StatusPublisher(WallclockTimeIntervalPublisher):
    def __init__(self, app, ES, time_status_step=None, time_status_init=None):
        super().__init__(app, time_status_step, time_status_init)
        self.ES = ES
        self.isInRange = False

    def publish_message(self):
        self.app.send_message(
            "state",
            SatelliteStatus(
                name=self.ES.name,
                geocentric_position=list(self.ES.geocentricPos),
                latitude=self.ES.geographicPos.latitude.degrees,
                longitude=self.ES.geographicPos.longitude.degrees,
                altitude=self.ES.geographicPos.elevation.m,
                velocity=list(self.ES.vel),
                time=self.ES.get_time(),
            ).json(),
        )
