from scipy.spatial.transform import Rotation as R
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from skyfield.api import load, wgs84, EarthSatellite, utc
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from schemas_with_target import *
from config import PARAMETERS

# initialize
targetQuat = PARAMETERS["targetQuat"]
Kp = PARAMETERS["Kp"]
Kd = PARAMETERS["Kd"]
initialQuat = PARAMETERS["initialQuat"]
T_c = PARAMETERS["initialT"]
I = PARAMETERS["I"]
dt = PARAMETERS["dt"]

# times for culmination
ts = load.timescale()
t_start = ts.from_datetime(datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc))
t_end = ts.from_datetime(datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(hours=PARAMETERS['SCENARIO_LENGTH']))

# dummy location
hoboken = wgs84.latlon(40.7440, -74.0324)

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
        self.omega = self.next_omega = None

        self.grounds = grounds
        self.target = self.next_target = None



    def initialize(self, init_time):

        super().initialize(init_time)
        self.target = [40.7440, -74.0324]            # lat/lon of Hoboken, NJ in degrees
        self.geocentric = self.ES.at(self.ts.from_datetime(init_time))
        self.pos = self.geocentric.position.m
        self.vel = self.geocentric.velocity.m_per_s
        
        # initial rotation from inertial to body coordinates
        posMag = np.linalg.norm(self.pos)            # position magnitude
        velMag = np.linalg.norm(self.vel)            # velocity magnitude  
        b_x = self.vel/velMag                        # body x-axis along velocity vector
        b_z = self.pos/posMag                        # body z-axis nadir pointing
        b_y = np.cross(b_x,b_z)                      # body y-axis normal to orbital plane
        dcm_0 = np.stack([b_x, b_y, b_z])            # initial dcm from inertial to body coordinates
        r = R.from_matrix(dcm_0)                     # creating rotation in scipy rotations library
        # self.att = r.as_quat()                       # initial quaternion from inertial to body coordinates
        self.att = np.array([0,0,0,1])
        self.omega = np.array([0,0,0])               # initial rotational velocity


    def tick(self, time_step): # computes
        super().tick(time_step)
        self.next_target = self.target #update_target(self, t_start, t_end)
        self.next_geocentric = self.ES.at(self.ts.from_datetime(self.get_time() + time_step))
        self.next_pos = self.next_geocentric.position.m
        self.next_vel = self.next_geocentric.velocity.m_per_s
        self.next_att = self.update_attitude(self)
        self.next_omega = self.omega



    def tock(self):
        self.target = self.next_target
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
    
    # find target quaternion at culmination from ground location
    def update_target(self, hoboken, t_start, t_end):
       
        t, events = ES.find_events(hoboken, t_start, t_end, altitude_degrees=30.0)
        eventZip = list(zip(t,events))
        df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
        culmTimes = df.loc[df["Event"]==2]
    
    # Calculate error between current quat and desired quat (Wie style)
    def att_error(self):
        qT = np.array(
            [
                [targetQuat[3], targetQuat[2], -targetQuat[1], -targetQuat[0]],
                [-targetQuat[2], targetQuat[3], targetQuat[0], -targetQuat[1]],
                [targetQuat[1], -targetQuat[0], targetQuat[3], -targetQuat[2]],
                [targetQuat[0], targetQuat[1], targetQuat[2], targetQuat[3]],
            ]
        )
        qB = np.array([self.att[0], self.att[1], self.att[2], self.att[3]])
        errorQuat = np.matmul(qT, qB)

        return errorQuat


    # Calculate torque produced by reaction wheels 
    def control_torque(self, errorQuat, Kp, Kd):  #Sidi
        
        T_c[0] = -(2 * Kp[0] * errorQuat[0] * errorQuat[3] + Kd[0] * self.omega[0])
        T_c[1] = -(2 * Kp[1] * errorQuat[1] * errorQuat[3] + Kd[1] * self.omega[1])
        T_c[2] = -(2 * Kp[2] * errorQuat[2] * errorQuat[3] + Kd[2] * self.omega[2])
    
        return T_c
    
    
    def quaternion_product(self, qwdt):
        x0 = self.att[0]
        y0 = self.att[1]
        z0 = self.att[2]
        w0 = self.att[3]
    
        x1 = qwdt[0]
        y1 = qwdt[1]
        z1 = qwdt[2]
        w1 = qwdt[3]
    
        xn = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
        yn = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
        zn = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1
        wn = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
        
        self.att = np.array([xn,yn,zn,wn])
    
        return self.att
    
    def update_attitude(self, time_step):
       
        # t, events = self.ES.find_events(hoboken, t_start, t_end, altitude_degrees=0.0)
        # event_names = 'rise above 30°', 'culminate', 'set below 30°'
        # for ti, event in zip(t, events):
        #    name = event_names[event]
        #    print(ti.utc_strftime('%Y %b %d %H:%M:%S'), name)
        #    print(type(event)) 
           
        t, events = self.ES.find_events(hoboken, t_start, t_end, altitude_degrees=30.0)
        eventZip = list(zip(t,events))
        df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
        culmTimes = df.loc[df["Event"]==2]
        print(events)
       
        # Calculate error quaternion
        errorQuat = self.att_error()
        
        # Calculate torque produced by reaction wheels
        T_c = self.control_torque(errorQuat, Kp, Kd)
        
        # Update angular velocity, euler angles, and quaternion
        alpha = np.matmul(np.linalg.inv(I), T_c)
        self.omega = self.omega + alpha * dt
        # eulerRad = eulerRad + self.omega * time_step
        # euler = np.degrees(eulerRad)
        qwdt = np.array(
            [
                ((self.omega[0] / np.linalg.norm(self.omega)) * np.sin(np.linalg.norm(self.omega) * dt / 2)),
                ((self.omega[1] / np.linalg.norm(self.omega)) * np.sin(np.linalg.norm(self.omega) * dt / 2)),
                ((self.omega[2] / np.linalg.norm(self.omega)) * np.sin(np.linalg.norm(self.omega) * dt / 2)),
                np.cos(np.linalg.norm(self.omega) * dt / 2)
            ]
        )

        self.att = self.quaternion_product(qwdt)
        
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
            self.satellite.get_time() + self.time_status_step
            )
        satSpaceTime = self.satellite.ES.at(next_time)
        subpoint = wgs84.subpoint(satSpaceTime)
        sensorRadius = self.satellite.get_sensor_radius()

        self.isInRange, groundId = self.satellite.check_in_range(self.satellite.grounds)
        
        self.app.send_message(
            "state",
            SatelliteStatus(
                id=self.satellite.id,
                name=self.satellite.name,
                position=list(self.satellite.pos),
                velocity=list(self.satellite.vel),
                attitude=list(self.satellite.att),
                omega = list(self.satellite.omega), #if self.satellite.att!=None else None,
                radius=sensorRadius,
                commRange=self.isInRange,
                time=self.satellite.get_time(),
            ).json(),
        )
