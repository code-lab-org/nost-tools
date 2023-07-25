from scipy.spatial.transform import Rotation as R
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from skyfield.api import load, wgs84, EarthSatellite, utc
from skyfield.framelib import itrs
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from schemas import SatelliteStatus
from config import PARAMETERS

# initialize
# targetQuat = PARAMETERS["targetQuat"]
Kp = PARAMETERS["Kp"]
Kd = PARAMETERS["Kd"]
initialQuat = PARAMETERS["initialQuat"]
T_c = PARAMETERS["initialT"]
I = PARAMETERS["I"]
dt = PARAMETERS["dt"]

# times for culmination
ts = load.timescale()
t_start = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc)
t_end  = datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=utc) + timedelta(hours=PARAMETERS['SCENARIO_LENGTH'])
# dummy location
targetLoc = wgs84.latlon(-35, -8)
# targetPos = targetLoc.itrs_xyz.m


class Satellite(Entity):
    def __init__(self, app, id, name, field_of_regard, grounds, tle):
        super().__init__(name)
        self.app = app
        self.ts = load.timescale()

        # if ES is not None:
        # self.ES = ES
        
        # if tle is not None:
        lines = tle.strip().splitlines()
        print(tle)
        self.ES = EarthSatellite(lines[1], lines[2], lines[0])
        print(EarthSatellite(lines[1], lines[2], lines[0]))
            
        self.id = id
        self.name = name
        self.field_of_regard = field_of_regard

        self.geocentric = self.next_geocentric = None
        self.pos_vel = self.next_pos_vel = None
        self.pos = self.next_pos = None
        self.vel = self.next_vel = None
        self.satLat = self.next_satLat = None
        self.satLon = self.next_satLon = None
        self.att = self.next_att = None
        self.omega = self.next_omega = None

        self.grounds = grounds
        self.target = self.next_target = None
        self.targetQuat = self.next_targetQuat = None

    def initialize(self, init_time):
        super().initialize(init_time)
        print(type(self.ES))
        self.target = [targetLoc]  
        self.geocentric = self.ES.at(self.ts.from_datetime(init_time))
        self.pos_vel= self.geocentric.frame_xyz_and_velocity(itrs)
        self.pos = self.pos_vel[0].m
        self.vel = self.pos_vel[1].m_per_s
        self.satLat = wgs84.geographic_position_of(self.geocentric).latitude.degrees
        self.satLon = wgs84.geographic_position_of(self.geocentric).longitude.degrees
        
        # initial nadir-pointing attitude
        h = np.cross(self.pos, self.vel)
        # Calculate the unit vectors for the body x, y, and z axes
        b_y = h / np.linalg.norm(h)  # body y-axis normal to orbital plane
        b_z = self.pos / np.linalg.norm(self.pos)  # body z-axis nadir pointing
        b_x0 = np.cross(b_y, b_z)
        b_x = b_x0 / np.linalg.norm(b_x0)  # body x-axis along velocity vector
        # Create the rotation matrix from the body to the inertial frame
        R_bi = np.vstack((b_x, b_y, b_z)).T
        self.att = self.targetQuat = R.from_matrix(
            R_bi
        ).as_quat()  # initial nadir-pointing quaternion from inertial to body coordinates
        self.omega = np.array([0, 0, 0])  # initial rotational velocity

    def tick(self, time_step):  # computes
        super().tick(time_step)
        self.next_target = self.target
        self.next_geocentric = self.ES.at(
            self.ts.from_datetime(self.get_time() + time_step)
        )
        self.next_pos_vel = self.next_geocentric.frame_xyz_and_velocity(itrs)
        self.next_pos = self.next_pos_vel[0].m
        self.next_vel = self.next_pos_vel[1].m_per_s
        self.next_satLat = wgs84.geographic_position_of(self.next_geocentric).latitude.degrees
        self.next_satLon = wgs84.geographic_position_of(self.next_geocentric).longitude.degrees
        self.next_subpoint = wgs84.geographic_position_of(self.next_geocentric)
        self.next_att = self.update_attitude(time_step, self.next_pos, self.next_vel)
        self.next_omega = self.omega
        self.next_targetQuat = self.update_target_attitude(
            self.next_pos, self.next_vel, targetLoc, t_start, t_end
        )

    def tock(self):
        self.target = self.next_target
        self.geocentric = self.next_geocentric
        self.pos_vel = self.next_pos_vel
        self.pos = self.next_pos
        self.vel = self.next_vel
        self.satLat = self.next_satLat
        self.satLon = self.next_satLon
        self.subpoint = self.next_subpoint
        self.att = self.next_att
        self.omega = self.next_omega
        self.targetQuat = self.next_targetQuat

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
        sin_rho = earth_mean_radius / (
            earth_mean_radius + wgs84.height_of(self.geocentric).m
        )
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
        sin_rho = earth_mean_radius / (
            earth_mean_radius + wgs84.height_of(self.geocentric).m
        )
        # eta is the nadir angle between the sub-satellite direction and the target location on the surface
        eta = np.degrees(
            np.arcsin(np.cos(np.radians(self.get_min_elevation())) * sin_rho)
        )
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
    
    def find_next_opportunity_time(self):
        # finding time, position, velocity of rise/culmination/set events
        print("OPP TIME TARGET LOC",targetLoc)
        t, events = self.ES.find_events(targetLoc, ts.from_datetime(t_start), ts.from_datetime(t_end), altitude_degrees=1.0)
        event_times = t.utc_datetime()
        eventZip = list(zip(event_times,events))
        df = pd.DataFrame(eventZip, columns = ["Time", "Event"])
        # removing rise/set events
        culmTimes = df.loc[df["Event"]==1]
        # dropping past culmination times from df
        next_opportunities_df = culmTimes.loc[culmTimes.Time > self.get_time()].copy()
        # setting first possible culmination time as next opportunity
        next_opportunity_time = ts.from_datetime(next_opportunities_df.iloc[0]["Time"])
        
        return next_opportunity_time 

    # find target quaternion at culmination from ground location
    def update_target_attitude(self, next_pos, next_vel, targetLoc, t_start, t_end):
        
        # nadir-pointing attitude
        h = np.cross(next_pos, next_vel)
        # Calculate the unit vectors for the body x, y, and z axes
        b_y = h / np.linalg.norm(h)
        b_z = next_pos / np.linalg.norm(next_pos)
        b_x0 = np.cross(b_y, b_z)
        b_x = b_x0 / np.linalg.norm(b_x0)
        # Create the rotation matrix from the body to the inertial frame
        R_bi = np.vstack((b_x, b_y, b_z)).T
        
        # finding satellite position and velocity at next opportunity
        next_opportunity_time = self.find_next_opportunity_time()
        culmGeocentric = self.ES.at(next_opportunity_time)
        pos_vel= culmGeocentric.frame_xyz_and_velocity(itrs)
        culm_pos = pos_vel[0].m
        culm_vel = pos_vel[1].m_per_s
        target_pos = targetLoc.itrs_xyz.m

        # find roll angle between nadir vector and target
        culmUnitVec = culm_pos / np.linalg.norm(culm_pos)
        direction = culm_pos - target_pos
        dirUnit = direction / np.linalg.norm(direction)

        rollAngle = np.arccos(np.dot(dirUnit, culmUnitVec))
        
        sat_geographical = wgs84.geographic_position_of(culmGeocentric)
        
        # rollAngle is always positive - need to fix when target is to right
        if culm_vel[2] > 0 and sat_geographical.longitude.degrees < targetLoc.longitude.degrees:
            rollAngle = -rollAngle
            
        if culm_vel[2] < 0 and sat_geographical.longitude.degrees > targetLoc.longitude.degrees:
            rollAngle = -rollAngle

        targetRot = R.from_matrix(R_bi) * R.from_euler("x", rollAngle)
        targetQuat = targetRot.as_quat()

        return targetQuat

    # Calculate error between current quat and desired quat (Wie style)
    def att_error(self, next_pos, next_vel):
        targetQuat = self.update_target_attitude(next_pos, next_vel, targetLoc, t_start, t_end
        )

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
        errorRot = R.from_quat(errorQuat)
        errorAngle = np.rad2deg((R.magnitude(errorRot)/(2*np.pi)))
        
        print("ERROR Angle IS",errorAngle)

        return errorQuat, errorAngle

    # Calculate torque produced by reaction wheels
    def control_torque(self, errorQuat, Kp, Kd):  # Sidi
        T_c[0] = -(2 * Kp[0] * errorQuat[0] * errorQuat[3] + Kd[0] * self.omega[0])
        T_c[1] = -(2 * Kp[1] * errorQuat[1] * errorQuat[3] + Kd[1] * self.omega[1])
        T_c[2] = -(2 * Kp[2] * errorQuat[2] * errorQuat[3] + Kd[2] * self.omega[2])
        print("TORQUE VECTOR", T_c)

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

        self.att = np.array([xn, yn, zn, wn])

        return self.att

    # changes the spacecraft's attitude
    def update_attitude(self, time_step, next_pos, next_vel):
        # Calculate error quaternion
        errorQuat, errorAngle = self.att_error(next_pos, next_vel)
        # Calculate torque produced by reaction wheels
        T_c = self.control_torque(errorQuat, Kp, Kd)
        # Update angular velocity, euler angles, and quaternion
        alpha = np.matmul(np.linalg.inv(I), T_c)
        self.omega = self.omega + alpha * dt
        # eulerRad = eulerRad + self.omega * time_step
        # euler = np.degrees(eulerRad)
        qwdt = np.array(
            [
                (
                    (self.omega[0] / np.linalg.norm(self.omega))
                    * np.sin(np.linalg.norm(self.omega) * dt / 2)
                ),
                (
                    (self.omega[1] / np.linalg.norm(self.omega))
                    * np.sin(np.linalg.norm(self.omega) * dt / 2)
                ),
                (
                    (self.omega[2] / np.linalg.norm(self.omega))
                    * np.sin(np.linalg.norm(self.omega) * dt / 2)
                ),
                np.cos(np.linalg.norm(self.omega) * dt / 2),
            ]
        )

        self.att = self.quaternion_product(qwdt)

        return self.att


# define a publisher to report satellite status
class StatusPublisher(WallclockTimeIntervalPublisher):
    def __init__(self, app, satellite, time_status_step=None, time_status_init=None):
        super().__init__(app, time_status_step, time_status_init)
        self.satellite = satellite
        self.isInRange = False

    def publish_message(self):
        # if self.satellite.att==None:
        #     return

        sensorRadius = self.satellite.get_sensor_radius()

        self.isInRange, groundId = self.satellite.check_in_range(self.satellite.grounds)

        self.app.send_message(
            "state",
            SatelliteStatus(
                id=self.satellite.id,
                name=self.satellite.name,
                position=list(self.satellite.pos),
                velocity=list(self.satellite.vel),
                latitude = self.satellite.satLat,
                longitude = self.satellite.satLon,
                attitude=list(self.satellite.att),
                angular_velocity=list(self.satellite.omega),
                target_quaternion=list(self.satellite.targetQuat),
                radius=sensorRadius,
                commRange=self.isInRange,
                time=self.satellite.get_time(),
            ).json(),
        )
