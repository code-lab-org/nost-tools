from scipy.spatial.transform import Rotation as R
import numpy as np

from skyfield.api import load, wgs84, EarthSatellite
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from schemas import *

class Satellite(Entity):


    def __init__(self, app, id, name, field_of_regard, grounds, ES=None, tle=None):
        super().__init__(name)
        self.app = app
        self.ts = load.timescale()

        if ES is not None: self.ES = ES
        if tle is not None: self.ES = EarthSatellite(tle[0], tle[1], name)

        self.id = id
        self.name = name
        self.field_of_regard = field_of_regard

        self.geocentric = None
        self.pos = self.next_pos = None
        self.vel = self.next_vel = None
        self.att = self.next_att = None

        self.grounds = grounds


    def initialize(self, init_time):

        super().initialize(init_time)
        self.geocentric = self.ES.at(self.ts.from_datetime(init_time))
        self.pos = self.geocentric.position.m
        self.vel = self.geocentric.velocity.m_per_s
        # initial attitude in geo coordinates
        # x along velocity vector
        # y normal to orbital plane
        # z nadir poiting (instrument)
        mag = np.linalg.norm(self.vel)
        self.att =  [x/mag for x in self.vel]


    def tick(self, time_step): # computes
        super().tick(time_step)
        self.next_geocentric = self.ES.at(self.ts.from_datetime(self.get_time()))
        self.next_pos = self.next_geocentric.position.m
        self.next_vel = self.next_geocentric.velocity.m_per_s
        self.next_att = self.att


    def tock(self):
        self.geocentric = self.next_geocentric
        self.pos = self.next_pos
        self.vel = self.next_vel
        self.att = self.next_att

        super().tock()


    def get_min_elevation(self):
        """
        Computes the minimum elevation angle required for the satellite to observe a point from current location.

        Returns:
            float : min_elevation
                The minimum elevation angle (degrees) for observation
        """
        earth_equatorial_radius = 6378137.000000000
        earth_polar_radius = 6356752.314245179
        earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3

        # eta is the angular radius of the region viewable by the satellite
        sin_eta = np.sin(np.radians(self.field_of_regard / 2))
        # rho is the angular radius of the earth viewed by the satellite
        sin_rho = earth_mean_radius / (earth_mean_radius + wgs84.height_of(self.geocentric).m)
        # epsilon is the min satellite elevation for obs (grazing angle)
        cos_epsilon = sin_eta / sin_rho
        if cos_epsilon > 1:
            return 0.0
        return np.degrees(np.arccos(cos_epsilon))


    def get_sensor_radius(self):
        """
        Computes the sensor radius for the satellite at current altitude given minimum elevation constraints.

        Returns:
            float : sensor_radius
                The radius (meters) of the nadir pointing sensors circular view of observation
        """
        earth_equatorial_radius = 6378137.0
        earth_polar_radius = 6356752.314245179
        earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
        # rho is the angular radius of the earth viewed by the satellite
        sin_rho = earth_mean_radius / (earth_mean_radius + wgs84.height_of(self.geocentric).m)
        # eta is the nadir angle between the sub-satellite direction and the target location on the surface
        eta = np.degrees(np.arcsin(np.cos(np.radians(self.get_min_elevation())) * sin_rho))
        # calculate swath width half angle from trigonometry
        sw_HalfAngle = 90 - eta - self.get_min_elevation()
        if sw_HalfAngle < 0.0:
            return 0.0
        return earth_mean_radius * np.radians(sw_HalfAngle)


    def get_elevation_angle(self, loc):
        """
        Returns the elevation angle (degrees) of satellite with respect to the topocentric horizon.

        Args:
            loc (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module

        Returns:
            float : alt.degrees
                Elevation angle (degrees) of satellite with respect to the topocentric horizon
        """
        difference = self.ES - loc
        topocentric = difference.at(self.ts.from_datetime(self.get_time()))
        # NOTE: Topos uses term altitude for what we are referring to as elevation
        alt, az, distance = topocentric.altaz()
        return alt.degrees


    def check_in_view(self, topos, min_elevation):
        """
        Checks if the elevation angle of the satellite with respect to the ground location is greater than the minimum elevation angle constraint.

        Args:
            topos (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module
            min_elevation (float): Minimum elevation angle (degrees) for ground to be in view of satellite, as calculated by compute_min_elevation

        Returns:
            bool : isInView
                True/False indicating visibility of ground location to satellite
        """
        isInView = False
        elevationFromEvent = self.get_elevation_angle(topos)
        if elevationFromEvent >= min_elevation:
            isInView = True
        return isInView


    def check_in_range(self, grounds):
        """
        Checks if the satellite is in range of any of the operational ground stations.

        Args:
            grounds (:obj:`DataFrame`): Dataframe of ground station locations, minimum elevation angles for communication, and operational status (T/F)

        Returns:
            bool, int :
                isInRange
                    True/False indicating visibility of satellite to any operational ground station
                groundId
                    groundId of the ground station currently in comm range (NOTE: If in range of two ground stations simultaneously, will return first groundId)
        """
        isInRange = False
        groundId = None
        for k, ground in grounds.iterrows():
            if ground.operational:
                groundLatLon = wgs84.latlon(ground.latitude, ground.longitude)
                satelliteElevation = self.get_elevation_angle(groundLatLon)
                if satelliteElevation >= ground.elevAngle:
                    isInRange = True
                    groundId = k
                    break
        return isInRange, groundId
    
    def normalize(self, vector):
        """Normalizes a vector so that its magnitude is 1
        
        Args:
            vector (numpy ndarray): an Nx1 vector of arbitrary magnitude
        
        Returns:
            numpy ndarray: the normalized vector
        """
        mag = np.linalg.norm(vector)
        if mag < np.finfo(np.float64).eps:
            return np.zeros(vector.shape)
        else:
            self.att = vector/mag
            return self.att

    def one_axis_control(self, time_step):  #fn in same class?
        """
        Updates the rotation about one axis the attitude"""

        r = R.from_euler('x', 1, degrees=True)
        r.as_matrix()
#        r.apply(self.att)

        return self.att


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
        sensorRadius = self.satellite.get_sensor_radius()

        self.isInRange, groundId = self.satellite.check_in_range(self.satellite.grounds)
        
        self.app.send_message(
            "location",
            SatelliteStatus(
                id=self.satellite.id,
                name=self.satellite.name,
                position=list(self.satellite.pos),
                velocity=list(self.satellite.vel),
                attitude=self.satellite.att, #if self.satellite.att!=None else None,
                radius=sensorRadius,
                commRange=self.isInRange,
                time=self.satellite.get_time(),
            ).json(),
        )
