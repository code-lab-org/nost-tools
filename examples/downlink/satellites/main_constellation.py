# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of satellites for monitoring fires propagated from Two-Line Elements (TLEs)*
    
    The application contains one :obj:`Constellation` (:obj:`Entity`) object class, one :obj:`PositionPublisher` (:obj:`WallclockTimeIntervalPublisher`), and two :obj:`Observer` object classes to monitor for :obj:`FireDetected` and :obj:`FireReported` events, respectively. The application also contains several methods outside of these classes, which contain standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson.

"""

import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
# import numpy as np
import pandas as pd
# import copy
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# import seaborn as sns

# from scipy import stats

# import time

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
# from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher

from skyfield.api import load, wgs84, EarthSatellite

from constellation_config_files.schemas import (
    SatelliteReady,
    SatelliteAllReady,
    SatelliteStatus,
    GroundLocation,
    LinkStart,
    LinkCharge
)
from constellation_config_files.config import (
    PREFIX,
    NAME,
    SCALE,
    # TLES,
    SSR_CAPACITY,
    CAPACITY_USED,
    INSTRUMENT_RATES
)

logging.basicConfig(level=logging.INFO)

# def compute_min_elevation(altitude, field_of_regard):
#     """
#     Computes the minimum elevation angle required for a satellite to observe a point from current location.

#     Args:
#         altitude (float): Altitude (meters) above surface of the observation.
#         field_of_regard (float): Angular width (degrees) of observation.

#     Returns:
#         float : min_elevation
#             The minimum elevation angle (degrees) for observation.
#     """
#     earth_equatorial_radius = 6378137.000000000
#     earth_polar_radius = 6356752.314245179
#     earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3

#     # eta is the angular radius of the region viewable by the satellite
#     sin_eta = np.sin(np.radians(field_of_regard / 2))
#     # rho is the angular radius of the earth viewed by the satellite
#     sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
#     # epsilon is the min satellite elevation for obs (grazing angle)
#     cos_epsilon = sin_eta / sin_rho
#     if cos_epsilon > 1:
#         return 0.0
#     return np.degrees(np.arccos(cos_epsilon))


# def compute_sensor_radius(altitude, min_elevation):
#     """
#     Computes the sensor radius for a satellite at current altitude given minimum elevation constraints.

#     Args:
#         altitude (float): Altitude (meters) above surface of the observation.
#         min_elevation (float): Minimum angle (degrees) with horizon for visibility.

#     Returns:
#         float : sensor_radius
#             The radius (meters) of the nadir pointing sensors circular view of observation.
#     """
#     earth_equatorial_radius = 6378137.0
#     earth_polar_radius = 6356752.314245179
#     earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
#     # rho is the angular radius of the earth viewed by the satellite
#     sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
#     # eta is the nadir angle between the sub-satellite direction and the target location on the surface
#     eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
#     # calculate swath width half angle from trigonometry
#     sw_HalfAngle = 90 - eta - min_elevation
#     if sw_HalfAngle < 0.0:
#         return 0.0
#     return earth_mean_radius * np.radians(sw_HalfAngle)


def get_elevation_angle(t, sat, loc):
    """
    Returns the elevation angle (degrees) of satellite with respect to the topocentric horizon

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


# def check_in_view(t, satellite, topos, min_elevation):
#     """
#     Checks if the elevation angle of the satellite with respect to the ground location is greater than the minimum elevation angle constraint

#     Args:
#         t (:obj:`Time`): Time object of skyfield.timelib module
#         satellite (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
#         topos (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module
#         min_elevation (float): Minimum elevation angle (degrees) for ground to be in view of satellite, as calculated by compute_min_elevation

#     Returns:
#         bool : isInView
#             True/False indicating visibility of ground location to satellite
#     """
#     isInView = False
#     elevationFromFire = get_elevation_angle(t, satellite, topos)
#     if elevationFromFire >= min_elevation:
#         isInView = True
#     return isInView


def check_in_range(t, satellite, grounds):
    """
    Checks if the satellite is in range of any of the operational ground stations

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        satellite (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
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
            satelliteElevation = get_elevation_angle(t, satellite, groundLatLon)
            if satelliteElevation >= ground.elevAngle:
                isInRange = True
                groundId = k
                break
    return isInRange, groundId


# define an entity to manage satellite updates
class Constellation(Entity):
    """
    *This object class inherits properties from the Entity object class in the NOS-T tools library*

    Args:
        cName (str): A string containing the name for the constellation application
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        id (:obj:`list`): List of unique *int* ids for each satellite in the constellation
        names (:obj:`list`): List of unique *str* for each satellite in the constellation (must be same length as **id**)
        ES (:obj:`list`): Optional list of :obj:`EarthSatellite` objects to be included in the constellation (NOTE: at least one of **ES** or **tles** MUST be specified, or an exception will be thrown)
        tles (:obj:`list`): Optional list of Two-Line Element *str* to be converted into :obj:`EarthSatellite` objects and included in the simulation
        
    Attributes:
        grounds (:obj:`DataFrame`): Dataframe containing information about ground stations with unique groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*) - *NOTE:* initialized as **None**
        satellites (:obj:`list`): List of :obj:`EarthSatellite` objects included in the constellation - *NOTE:* must be same length as **id**
        positions (:obj:`list`): List of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
        next_positions (:obj:`list`): List of next latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
        
    """

    ts = load.timescale()
    PROPERTY_POSITION = "position"
    PROPERTY_LINKCHARGE = "linkCharge"

    def __init__(self, cName, app, id, names, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.id = id
        self.names = names
        self.groundTimes = {j:[] for j in self.names}
        self.grounds = None
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
        self.ssr_capacity = SSR_CAPACITY
        self.capacity_used = CAPACITY_USED
        self.instrument_rates = INSTRUMENT_RATES
        self.linkCounts = [0 for satellite in self.satellites]
        self.linkStatus = [False for satellite in self.satellites]

    def initialize(self, init_time):
        """
        Activates the :obj:`Constellation` at a specified initial scenario time
        
        Args:
            init_time (:obj:`datetime`): Initial scenario time for simulating propagation of satellites
        """
        super().initialize(init_time)
        self.grounds = pd.DataFrame(
            {
                "groundId": pd.Series([], dtype="int"),
                "latitude": pd.Series([], dtype="float"),
                "longitude": pd.Series([], dtype="float"),
                "elevAngle": pd.Series([], dtype="float"),
                "operational": pd.Series([], dtype="bool"),
                "downlinkRate": pd.Series([], dtype="float"),
                "costPerSecond": pd.Series([], dtype="float")
            }
        )
        self.positions = self.next_positions = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]
        
        for i, satellite in enumerate(self.satellites):
            
            self.app.send_message(
                "ready",
                SatelliteReady(
                    id=self.id[i],
                    name=self.names[i],
                    ssr_capacity=self.ssr_capacity[i]
                ).json()
            )
        self.app.send_message("allReady", SatelliteAllReady().json())

    def tick(self, time_step):
        """
        Computes the next :obj:`Constellation` state after the specified scenario duration and the next simulation scenario time
        
        Args:
            time_step (:obj:`timedelta`): Duration between current and next simulation scenario time
        """
        # tik = time.time()
        super().tick(time_step)
        self.next_positions = [
            wgs84.subpoint(
                satellite.at(self.ts.from_datetime(self.get_time() + time_step))
            )
            for satellite in self.satellites
        ]
        for i, satellite in enumerate(self.satellites):
            then = self.ts.from_datetime(self.get_time() + time_step)
            isInRange, groundId = check_in_range(then, satellite, self.grounds)
            self.capacity_used[i] = self.capacity_used[i] + ((self.instrument_rates[i]*time_step.total_seconds())/self.ssr_capacity[i])
            if isInRange:
                if not self.linkStatus[i]:
                    self.linkStatus[i] = True
                    self.linkCounts[i] = self.linkCounts[i] + 1
            else:
                if self.linkStatus[i]:
                    self.linkStatus[i] = False

    def tock(self):
        """
        Commits the next :obj:`Constellation` state and advances simulation scenario time
        
        """
        # tik = time.time()
        self.positions = self.next_positions
        super().tock()

    def on_ground(self, client, userdata, message):
        """
        Callback function appends a dictionary of information for a new ground station to grounds :obj:`list` when message detected on the *PREFIX/ground/location* topic. Ground station information is published at beginning of simulation, and the :obj:`list` is converted to a :obj:`DataFrame` when the Constellation is initialized.
        
        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
            
        """
        location = GroundLocation.parse_raw(message.payload)
        if location.groundId in self.grounds.groundId:
            self.grounds[
                self.grounds.groundId == location.groundId
            ].latitude = location.latitude
            self.grounds[
                self.grounds.groundId == location.groundId
            ].longitude = location.longitude
            self.grounds[
                self.grounds.groundId == location.groundId
            ].elevAngle = location.elevAngle
            self.grounds[
                self.grounds.groundId == location.groundId
            ].operational = location.operational
            self.grounds[
                self.grounds.groundId == location.groundId
            ].downlinkRate = location.downlinkRate
            self.grounds[
                self.grounds.groundId == location.groundId
            ].costPerSecond = location.costPerSecond
            print(f"Station {location.groundId} updated at time {self.get_time()}.")
        else:
            self.grounds = self.grounds.append(
                {
                    "groundId": location.groundId,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "elevAngle": location.elevAngle,
                    "operational": location.operational,
                    "downlinkRate": location.downlinkRate,
                    "costPerSecond": location.costPerSecond
                },
                ignore_index=True,
            )
            print(f"Station {location.groundId} registered at time {self.get_time()}.")
            
    def on_linkStart(self, client, userdata, message):
        """
        Callback function when message detected on the *PREFIX/ground/linkStart* topic.
        
        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
            
        """
        downlinkStart = LinkStart.parse_raw(message.payload)
        print(downlinkStart)
        self.groundTimes[downlinkStart.satName].append(
            {
                "groundId":downlinkStart.groundId,
                "satId":downlinkStart.satId,
                "satName":downlinkStart.satName,
                "linkId":downlinkStart.linkId,
                "start":downlinkStart.start,
                "end":None,
                "duration":None,
                "initialData": downlinkStart.data,
                "dataOffload":None,
                "downlinkCost":None
            },
        )
    
    def on_linkCharge(self, client, userdata, message):
       """
       Callback function when message detected on the *PREFIX/ground/linkCharge* topic.
       
       Args:
           client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
           userdata: User defined data of any type (not currently used)
           message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
           
       """
       downlinkCharge = LinkCharge.parse_raw(message.payload)
       self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["end"] = downlinkCharge.end
       self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["duration"] = downlinkCharge.duration
       self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["dataOffload"] = downlinkCharge.dataOffload
       self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["downlinkCost"] = downlinkCharge.downlinkCost
       self.capacity_used[downlinkCharge.satId] = self.capacity_used[downlinkCharge.satId] - (downlinkCharge.dataOffload / self.ssr_capacity[downlinkCharge.satId])
       if self.capacity_used[downlinkCharge.satId] < 0:
           self.capacity_used[downlinkCharge.satId] = 0


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
        self.isInRange = [
            False for i, satellite in enumerate(self.constellation.satellites)
        ]

    def publish_message(self):
        """
        *Abstract publish_message method inherited from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*
        
        This method sends a message to the *PREFIX/constellation/location* topic for each satellite in the constellation (:obj:`Constellation`), including:
            
        Args:
            id (:obj:`list`): list of unique *int* ids for each satellite in the constellation
            names (:obj:`list`): list of unique *str* for each satellite in the constellation - *NOTE:* must be same length as **id**
            positions (:obj:`list`): list of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
            radius (:obj:`list`): list of the radius (meters) of the nadir pointing sensors circular view of observation for each satellite in the constellation - *NOTE:* must be same length as **id**
            commRange (:obj:`list`): list of *bool* indicating each satellites visibility to *any* ground station - *NOTE:* must be same length as **id**
            time (:obj:`datetime`): current scenario :obj:`datetime`

        """
        for i, satellite in enumerate(self.constellation.satellites):
            next_time = constellation.ts.from_datetime(
                constellation.get_time() + 60 * self.time_status_step
            )
            satSpaceTime = satellite.at(next_time)
            subpoint = wgs84.subpoint(satSpaceTime)
            self.isInRange[i], groundId = check_in_range(
                next_time, satellite, constellation.grounds
            )
            self.app.send_message(
                "location",
                SatelliteStatus(
                    id=i,
                    name=self.constellation.names[i],
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude=subpoint.elevation.m,
                    capacity_used=self.constellation.capacity_used[i],
                    commRange=self.isInRange[i],
                    groundId=groundId,
                    totalLinkCount=self.constellation.linkCounts[i],
                    time=constellation.get_time(),
                ).json(),
            )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = "testbed.mysmce.com", 8883
    USERNAME, PASSWORD = "bchell", "cT8T1pd62KnZ"
    
    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication(NAME)

    # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    activesats = load.tle_file(activesats_url, reload=True)

    # keys for CelesTrak TLEs used in this example, but indexes often change over time)
    names = ["SUOMI NPP (VIIRS)", "NOAA 20 (VIIRS)"]
    NPP = activesats[541]
    NOAA20 = activesats[1293]
    ES = [NPP, NOAA20]
    

    # initialize the Constellation object class (in this example from EarthSatellite type)
    constellation = Constellation("constellation", app, [0, 1], names, ES)

    # add observer classes to the Constellation object class
    # constellation.add_observer(FireReportedObserver(app))

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(constellation)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(
        PositionPublisher(app, constellation, timedelta(seconds=1))
    )

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2020, 10, 24, 7, 20, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )

    # add message callbacks
    app.add_message_callback("ground", "location", constellation.on_ground)
    app.add_message_callback("ground", "linkStart", constellation.on_linkStart)
    app.add_message_callback("ground", "linkCharge", constellation.on_linkCharge)