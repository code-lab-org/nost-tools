from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.framelib import itrs
import numpy as np
import logging
import pandas as pd

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher

from constellation_config_files.schemas import SatelliteStatus
from constellation_config_files.config import PREFIX, NAME, SCALE, TLES, FIELD_OF_REGARD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def get_elevation_angle(t, sat, loc):
    """
    Returns the elevation angle (degrees) of satellite with respect to the topocentric horizon.

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        sat (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
        loc (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module

    Returns:
        float : alt.degrees
            Elevation angle (degrees) of satellite with respect to the topocentric horizon
    """
    difference = sat - loc
    topocentric = difference.at(t)
    # NOTE: Topos uses term altitude for what we are referring to as elevation
    alt, az, distance = topocentric.altaz()
    return alt.degrees

def compute_sensor_radius(altitude, min_elevation):
    """
    Computes the sensor radius for a satellite at current altitude given minimum elevation constraints.

    Args:
        altitude (float): Altitude (meters) above surface of the observation
        min_elevation (float): Minimum angle (degrees) with horizon for visibility

    Returns:
        float : sensor_radius
            The radius (meters) of the nadir pointing sensors circular view of observation
    """
    earth_equatorial_radius = 6378137.0
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    # eta is the nadir angle between the sub-satellite direction and the target location on the surface
    eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
    # calculate swath width half angle from trigonometry
    sw_HalfAngle = 90 - eta - min_elevation
    if sw_HalfAngle < 0.0:
        return 0.0
    return earth_mean_radius * np.radians(sw_HalfAngle)

class Constellation(Entity):
    ts = load.timescale()
    PROPERTY_POSITION = "position"

    def __init__(self, cName, app, id, names, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.id = id
        self.names = names
        self.satellites = []
        if ES is not None:
            for satellite in ES:
                self.satellites.append(satellite)
        if tles is not None:
            for i, tle in enumerate(tles):
                self.satellites.append(
                    EarthSatellite(tle[0], tle[1], self.names[i], self.ts)
                )
        self.positions = self.next_positions = [None for satellite in self.satellites]

    def initialize(self, init_time):
        super().initialize(init_time)
        self.positions = self.next_positions = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]

    # def tick(self, time_step):
    #     super().tick(time_step)
    #     self.next_positions = [
    #         wgs84.subpoint(
    #             satellite.at(self.ts.from_datetime(self.get_time() + time_step))
    #         )
    #         for satellite in self.satellites
    #     ]

    # def tock(self):
    #     self.positions = self.next_positions
    #     for i, satellite in enumerate(self.satellites):
    #         current_time = self.ts.from_datetime(self.get_time())
    #         position = satellite.at(current_time)
    #         subpoint = wgs84.subpoint(position)
    #         altitude_meters = subpoint.elevation.m
    #         velocity = position.velocity.km_per_s
    #         velocity_x, velocity_y, velocity_z = velocity
    #         sensor_radius_meters = compute_sensor_radius(altitude_meters, 0)
    #         # logger.info(f"Message sent: {subpoint.longitude.degrees}")
    #         self.app.send_message(
    #             self.app.app_name,
    #             "location",
    #             SatelliteStatus(
    #                 id=i,
    #                 name=satellite.name,
    #                 latitude=subpoint.latitude.degrees,
    #                 longitude=subpoint.longitude.degrees,
    #                 altitude=altitude_meters,
    #                 radius=sensor_radius_meters,
    #                 # velocity = {velocity_x, velocity_y, velocity_z},
    #                 commRange=False,  # Assuming no ground stations for simplicity
    #                 time=self.get_time(),
    #             ).json(),
    #         )
    #     super().tock()

# define a publisher to report satellite status
class PositionPublisher(WallclockTimeIntervalPublisher):
    """
    *This object class inherits properties from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

    The user can optionally specify the wallclock :obj:`timedelta` between message publications and the scenario :obj:`datetime` when the first of these messages should be published.

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        constellation (:obj:`Constellation`): Constellation :obj:`Entity` object class
        time_status_step (:obj:`timedelta`): Optional duration between time status 'heartbeat' messages
        time_status_init (:obj:`datetime`): Optional scenario :obj:`datetime` for publishing the first time status 'heartbeat' message

    """

    def __init__(
        self, app, constellation, time_status_step=None, time_status_init=None
    ):
        super().__init__(app, time_status_step, time_status_init)
        self.constellation = constellation

        if self.time_status_init is None:
            self.time_status_init = self.constellation.ts.now().utc_datetime()
        
        # self.isInRange = [
        #     False for i, satellite in enumerate(self.constellation.satellites)
        # ]

    def publish_message(self):
        """
        *Abstract publish_message method inherited from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

        This method sends a :obj:`SatelliteStatus` message to the *PREFIX/constellation/location* topic for each satellite in the constellation (:obj:`Constellation`).

        """
        current_time = constellation.get_time()
        elapsed_seconds = (current_time - self.time_status_init).total_seconds()
        current_minute = (elapsed_seconds // 60) % 100
        
        swath_data = {
            'CAPELLA-14 (ACADIA-4)': 30, # Swath value in km 
            'GCOM-W1 (SHIZUKU)': 1450 # Swath value in km
            }
        
        for i, satellite in enumerate(self.constellation.satellites):
            next_time = constellation.ts.from_datetime(
                constellation.get_time() + 60 * self.time_status_step
            )
            # logger.info(f"Next time: {next_time}; Satellite: {satellite.name}")
            satSpaceTime = satellite.at(next_time)
            subpoint = wgs84.subpoint(satSpaceTime)
            # lat, lon = subpoint.latitude, subpoint.longitude
            # altitude_meters = subpoint.elevation.m

            if satellite.name=='CAPELLA-14 (ACADIA-4)':
                state = current_minute < 1
            elif satellite.name=='GCOM-W1 (SHIZUKU)':
                state = True

            # # Determine if the satellite is above the horizon (scanning)
            # alt, az, distance = satSpaceTime.altaz()
            # if alt.degrees > 0:
            #     scanning = True
            # else:
            #     scanning = False

            # Get the cartesian posotion of the satellite
            x, y, z = satSpaceTime.frame_xyz(itrs).m
            ecef_position = satSpaceTime.position.m
            ecef_x, ecef_y, ecef_z = ecef_position

            # Get the velocity of the satellite
            velocity = satSpaceTime.velocity.km_per_s
            velocity_x, velocity_y, velocity_z = velocity

            #Get the angular width of the satellite
            sensorRadius = compute_sensor_radius(
                subpoint.elevation.m, 0
            )

            # self.isInRange[i], groundId = check_in_range(
            #     next_time, satellite, constellation.grounds
            # )
            self.app.send_message(
                self.app.app_name,
                "location",
                SatelliteStatus(
                    id=i,
                    name=satellite.name,
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude=subpoint.elevation.m,
                    radius=sensorRadius,
                    velocity=[velocity_x, velocity_y, velocity_z],
                    state=state,
                    swath=swath_data.get(satellite.name, 0),
                    # commRange=self.isInRange[i],
                    time=constellation.get_time(),
                    ecef=[x, y, z],
                ).json(),
            )

if __name__ == "__main__":
    credentials = dotenv_values(".env")
    HOST, RABBITMQ_PORT, KEYCLOAK_PORT = credentials["HOST"], int(credentials["RABBITMQ_PORT"]), int(credentials["KEYCLOAK_PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    CLIENT_ID = credentials["CLIENT_ID"]
    CLIENT_SECRET_KEY = credentials["CLIENT_SECRET_KEY"]
    VIRTUAL_HOST = credentials["VIRTUAL_HOST"]
    IS_TLS = credentials["IS_TLS"].lower() == 'true'

    config = ConnectionConfig(
        USERNAME,
        PASSWORD,
        HOST,
        RABBITMQ_PORT,
        KEYCLOAK_PORT,
        CLIENT_ID,
        CLIENT_SECRET_KEY,
        VIRTUAL_HOST,
        IS_TLS)

    app = ManagedApplication(NAME)

    activesats_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    activesats = load.tle_file(activesats_url, reload=False)

    by_name = {sat.name: sat for sat in activesats}
    names = ['CAPELLA-14 (ACADIA-4)', 'GCOM-W1 (SHIZUKU)'] #'CAPELLA-14 (ACADIA)'

    ES = []
    indices = []
    for name_i, name in enumerate(names):
        name = str(name).strip()
        if name in by_name:
            ES.append(by_name[name])
            indices.append(name_i)
        else:
            logger.warning(f"Key '{name}' does not exist in the 'by_name' dictionary.")

    constellation = Constellation("constellation", app, indices, names, ES)
    app.simulator.add_entity(constellation)
    app.simulator.add_observer(ShutDownObserver(app))
    app.simulator.add_observer(PositionPublisher(app, constellation, timedelta(seconds=1)))

    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime.now(timezone.utc), #datetime(2020, 1, 1, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
        # shut_down_when_terminated=True,
    )

    # while True:
    #     pass