# -*- coding: utf-8 -*-
"""
    *This application template models a satellite's orbit and view of Earth*

    The template contains two classes, the :obj:`Satellite` (:obj:`Entity`) object class and the one :obj:`StatusPublisher` (:obj:`WallclockTimeIntervalPublisher`) class. The template also adds several methods within these classes.

"""

import numpy as np

from skyfield.api import load, wgs84, EarthSatellite
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from schemas import *


class Satellite(Entity):

    """
    *This object class inherits properties from the Entity object class in the NOS-T tools library*

    Args:
        Name (str): A string containing the name for the satellite application
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        id (list): List of unique *int* ids for each satellite
        ES (list): Optional :obj:`EarthSatellite` object to be included (NOTE: at least one of **ES** or **tles** MUST be specified, or an exception will be thrown)\n
        tles (list): Optional Two-Line Element *str* to be converted into :obj:`EarthSatellite` objects and included in the simulation

    Attributes:
        geoPos (list): List of current geocentric XYZ inertial coordinates (:obj:`Distance`) of the satellite
        next_geoPos (list): List of next geocentric XYZ inertial coordinates (:obj:`Distance`) of the satellite
        pos (list): List of current latitude-longitude-altitude (:obj:`GeographicPosition`) of the satellite
        next_pos (list): List of next latitude-longitude-altitude (:obj:`GeographicPosition`) of the satellite
        vel (list): List of current velocity in geocentric XYZ vector elements (:obj:`Velocity`) of the satellite
        next_vel (list): List of next velocity in geocentric XYZ vector elements (:obj:`Velocity`) of the satellite
    """

    def __init__(self, app, id, name, field_of_regard, grounds, ES=None, tle=None):
        super().__init__(name)
        self.app = app
        self.ts = load.timescale()

        if ES is not None:
            self.ES = ES
        if tle is not None:
            self.ES = EarthSatellite(tle[0], tle[1], name)

        self.id = id
        self.name = name
        self.field_of_regard = field_of_regard
        self.geoPos = self.next_geoPos = None
        self.pos = self.next_pos = None
        self.vel = self.next_vel = None

        self.grounds = grounds

    def initialize(self, init_time):
        """
        Activates the :obj:`Satellite` at a specified initial scenario time

        Args:
            init_time (:obj:`datetime`): Initial scenario time for simulating propagation of satellites
        """

        super().initialize(init_time)
        self.geocentric = self.ES.at(self.ts.from_datetime(init_time))
        self.geoPos = self.geocentric.position.m
        self.pos = wgs84.subpoint(ES.at(self.ts.from_datetime(init_time)))
        self.vel = self.geocentric.velocity.m_per_s

    def tick(self, time_step):
        """
        Computes the next :obj:`Satellite` state after the specified scenario duration and the next simulation scenario time

        Args:
            time_step (:obj:`timedelta`): Duration between current and next simulation scenario time
        """
        super().tick(time_step)

        self.next_geocentric = self.ES.at(self.ts.from_datetime(self.get_time()))
        self.next_geoPos = self.next_geocentric.position.m
        self.next_pos = wgs84.subpoint(self.ts.from_datetime(self.get_time()))
        self.next_vel = self.next_geocentric.velocity.m_per_s

    def tock(self):
        """
        Commits the next :obj:`Satellite` state and advances simulation scenario time

        """

        self.geoPos = self.next_geoPos
        self.pos = self.next_pos
        self.vel = self.next_vel

        super().tock()

# define a publisher to report satellite status
class StatusPublisher(WallclockTimeIntervalPublisher):
    def __init__(self, app, satellite, time_status_step=None, time_status_init=None):
        super().__init__(app, time_status_step, time_status_init)
        self.satellite = satellite
        self.isInRange = False

    def publish_message(self):
        next_time = self.satellite.ts.from_datetime(
            self.satellite.get_time() + 60 * self.time_status_step
        )
        satSpaceTime = self.satellite.ES.at(next_time)
        subpoint = wgs84.subpoint(satSpaceTime)

        self.app.send_message(
            "location",
            SatelliteStatus(
                id=self.satellite.id,
                name=self.satellite.name,
                geocentric_position=list(self.satellite.geoPos),
                geographical_position=list(self.satellite.pos),
                velocity=list(self.satellite.vel),
                time=self.satellite.get_time(),
            ).json(),
        )
