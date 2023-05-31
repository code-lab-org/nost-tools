import os
import sys
import logging
import numpy as np
import pandas as pd
import copy
import datetime

from skyfield.api import load, wgs84, EarthSatellite
from skyfield import almanac
from nost_tools.entity import Entity
from nost_tools.observer import Observer
from nost_tools.publisher import WallclockTimeIntervalPublisher

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
superparent = os.path.dirname(parent)

sys.path.append(superparent)
sys.path.append(parent)

from schemas import *


def compute_min_elevation(altitude, field_of_regard):
    """
    Computes the minimum elevation angle required for a satellite to observe a point from current location.

    Args:
        altitude (float): Altitude (meters) above surface of the observation
        field_of_regard (float): Angular width (degrees) of observation

    Returns:
        float : min_elevation
            The minimum elevation angle (degrees) for observation
    """
    earth_equatorial_radius = 6378137.000000000
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3

    # eta is the angular radius of the region viewable by the satellite
    sin_eta = np.sin(np.radians(field_of_regard / 2))
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    # epsilon is the min satellite elevation for obs (grazing angle)
    cos_epsilon = sin_eta / sin_rho
    if cos_epsilon > 1:
        return 0.0
    return np.degrees(np.arccos(cos_epsilon))


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


def check_in_view(t, satellite, topos, min_elevation):
    """
    Checks if the elevation angle of the satellite with respect to the ground location is greater than the minimum elevation angle constraint.

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        satellite (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
        topos (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module
        min_elevation (float): Minimum elevation angle (degrees) for ground to be in view of satellite, as calculated by compute_min_elevation

    Returns:
        bool : isInView
            True/False indicating visibility of ground location to satellite
    """
    isInView = False
    elevationFromEvent = get_elevation_angle(t, satellite, topos)
    if elevationFromEvent >= min_elevation:
        isInView = True
    return isInView


def check_in_range(t, satellite, grounds):
    """
    Checks if the satellite is in range of any of the operational ground stations.

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
        cName (:obj:`str`): A string containing the name for the constellation application
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        field_of_regard (:obj:`List`): A list of the fields of regard for each satellite in the constellation
        night_sight (:obj:`bool`): A boolean value specifying whether or not the constellation can observe events at night. default=True
        ES (list): Optional list of :obj:`EarthSatellite` objects to be included in the constellation (NOTE: at least one of **ES** or **tles** MUST be specified, or an exception will be thrown)\n
        tles (list): Optional list of Two-Line Element *str* to be converted into :obj:`EarthSatellite` objects and included in the simulation
        
    Attributes:
        events (:obj:`DataFrame`): Events with unique eventId (:obj:`int`), latitude (:obj:`float`), longitude (:obj:`float`) and day/night status (:obj:`bool`) - *NOTE:* initialized as empty :obj:`DataFrame`
        grounds (:obj:`DataFrame`): Dataframe containing information about ground stations with unique groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*) - *NOTE:* initialized as **None**
        satellites (:obj:`list`): List of :obj:`EarthSatellite` objects included in the constellation
        sat_data (:obj:`list`): List of the ids of detected events not yet reported. Is set to [ ] when events are reported to groundstation
        new_detect (:obj:`list`): List of events detected at the current timestep with unique eventId (*int*), detected :obj:`datetime`, and name (*str*) of detecting satellite - *NOTE:* initialized as [ ]
        new_report (:obj:`list`): List of events reported at the current timestep with unique eventId (*int*), reported :obj:`datetime`, name (*str*) of reporting satellite, and groundId (*int*) of ground station reported to - *NOTE:* initialized as [ ]
        positions (:obj:`list`): List of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation
        next_positions (:obj:`list`): List of next latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation
        min_elevations_event (:obj:`list`): List of :obj:`float` indicating current elevation angle (degrees) constraint for visibility by each satellite
    """

    # Parameters used for internal Skyfield calculations
    ts = load.timescale()
    eph = load('de421.bsp')


    def __init__(self, cName, app, field_of_regard, night_sight=True, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.tles=tles
        self.field_of_regard = field_of_regard
        self.night_sight = night_sight

        # Initalize empty event DataFrame
        self.events = pd.DataFrame(
            data={
                "eventId": [],
                "latitude": [],
                "longitude": [],
                "isDay": [],
            }
        )
        # Set DataFrame index to eventId column
        self.events.set_index("eventId", inplace=True)
        self.grounds = None

        # Checks whether tles or EarthSatellite objects were provided, and builds self.satellites from either
        self.satellites = []
        if ES is not None:
            for satellite in ES:
                self.satellites.append(satellite)
        if self.tles is not None:
            for name in self.tles.keys():
                self.satellites.append(
                    EarthSatellite(self.tles[name][0], self.tles[name][1], name, self.ts)
                )
        print(self.tles)
        print(self.satellites)
        self.sat_data = {sat.name: [] for sat in self.satellites}
        self.new_detect = []
        self.new_report = []
        self.positions = self.next_positions = [None for _ in self.satellites]
        self.min_elevations_event = [
            compute_min_elevation(
                wgs84.subpoint(satellite.at(satellite.epoch)).elevation.m,
                self.field_of_regard[i],
            )
            for i, satellite in enumerate(self.satellites)
        ]
        # # Two print lines below can be used as sanity check that SMAD Ch. 5 equations implemented properly
        # print("\nInitial elevation angles:\n")
        # print(self.min_elevations_event)


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
            }
        )
        self.positions = self.next_positions = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]


    def tick(self, time_step):
        """
        Computes the next :obj:`Constellation` state after the specified scenario duration and the next simulation scenario time
        
        Args:
            time_step (:obj:`timedelta`): Duration between current and next simulation scenario time
        """

        super().tick(time_step)

        # Calculate all satellite positions at the following timestep
        self.next_positions = [
            wgs84.subpoint(
                satellite.at(self.ts.from_datetime(self.get_time() + time_step))
            )
            for satellite in self.satellites
        ]
        
        time=self.satellite.at(self.ts.from_datetime(self.get_time() + time_step))
    
        
        print("THE LATITUDE IS", self.next_positions)
        
        
        
        # for i, satellite in enumerate(self.constellation.satellites):
        #     next_time = self.constellation.ts.from_datetime(
        #         self.constellation.get_time() + 60 * self.time_status_step
        #     )
        #     satSpaceTime = satellite.at(next_time)
        #     subpoint = wgs84.subpoint(satSpaceTime)
        #     sensorRadius = compute_sensor_radius(
        #         subpoint.elevation.m, self.constellation.min_elevations_event[i]
        #     )
        #     self.isInRange[i], groundId = check_in_range(
        #         next_time, satellite, self.constellation.grounds
        #     )
        #     self.app.send_message(
        #         "location",
        #         SatelliteStatus(
        #             id=i,
        #             name=satellite.name,
        #             latitude=subpoint.latitude.degrees,
        #             longitude=subpoint.longitude.degrees,
        #             altitude=subpoint.elevation.m,
        #             radius=sensorRadius,
        #             commRange=self.isInRange[i],
        #             time=self.constellation.get_time(),
        #         ).json(),
        #     )
        

        # Loop over satellites
        for i, satellite in enumerate(self.satellites):
            then = self.ts.from_datetime(self.get_time() + time_step)
            now = self.ts.from_datetime(self.get_time())

            # Compute elevation angle required for satellite to be able to observe an event
            self.min_elevations_event[i] = compute_min_elevation(
                float(self.next_positions[i].elevation.m), self.field_of_regard[i]
            )

            # Checks if satellite is in range of any ground stations
            isInRange, groundId = check_in_range(then, satellite, self.grounds)




    def tock(self):
        """
            Publishes new detections and reports and advances simulation scenario time
        
        """

        # Advances positions
        self.positions = self.next_positions
        
        # Notifies observers of each newly detected event
        for event_change in self.new_detect:
            self.notify_observers(
                'detected',
                None,
                {
                    "eventId": event_change["eventId"],
                    "detected": event_change["detected"],
                    "detected_by": event_change["detected_by"]
                }
            )

        # Notifies observers of each newly detected event
        for event_change in self.new_report:
            self.notify_observers(
                "reported",
                None,
                {
                    "eventId": event_change["eventId"],
                    "reported": event_change["reported"],
                    "reported_by": event_change["reported_by"],
                    "reported_to": event_change["reported_to"]
                }
            )
        
        # Reset detection and report lists for next timestep
        self.new_detect = []
        self.new_report = []

        super().tock()


    def on_manager_init(self, client, userdata, message):
        """
            *PREFIX/manager/init* callback to publish constellation Two-Line Elements to be recorded for repeatability in future simulations
            
            Args:
                client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
                userdata: User defined data of any type (not currently used)
                message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
        """
        self.app.send_message("tles", self.tles.to_json())

    def on_event_start(self, client, userdata, message):
        """
        *PREFIX/events/start* callback function appends a dictionary of information for a new event to events :obj:`DataFrame`
        
        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
            
        """
        started = EventStarted.parse_raw(message.payload)
        self.events.loc[started.eventId] = {
            "latitude": started.latitude,
            "longitude": started.longitude,
            "isDay": started.isDay
        }

    def on_event_day_change(self, client, userdata, message):
        """
            *PREFIX/event/dayChange* callback to update event day/night status

            Args:
                client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
                userdata: User defined data of any type (not currently used)
                message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
        """
        change = EventDayChange.parse_raw(message.payload)
        self.events["isDay"][change.eventId] = change.isDay

    def on_event_finish(self, client, userdata, message):
        """
            *PREFIX/event/finish* callback to remove finished events from events :obj:`DataFrame`

            Args:
                client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
                userdata: User defined data of any type (not currently used)
                message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes 
        """
        finished = EventFinished.parse_raw(message.payload)
        self.events.drop(finished.eventId)


    def on_ground(self, client, userdata, message):
        """
            *PREFIX/ground/location* callback function appends a dictionary of information for a new ground station to grounds :obj:`list`. Ground station information is published at beginning of simulation, and the :obj:`list` is converted to a :obj:`DataFrame` when the Constellation is initialized.
        
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
        else:
            self.grounds = self.grounds.append(
                {
                    "groundId": location.groundId,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "elevAngle": location.elevAngle,
                    "operational": location.operational,
                },
                ignore_index=True,
            )


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
            False for _ in self.constellation.satellites
        ]

    def publish_message(self):
        """
        *Abstract publish_message method inherited from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*
        
        This method sends a message to the *PREFIX/constellation/location* topic for each satellite in the constellation (:obj:`Constellation`), including:
            
        Args:
            id (list): list of unique *int* ids for each satellite in the constellation
            names (list): list of unique *str* for each satellite in the constellation - *NOTE:* must be same length as **id**
            positions (list): list of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
            radius (list): list of the radius (meters) of the nadir pointing sensors circular view of observation for each satellite in the constellation - *NOTE:* must be same length as **id**
            commRange (list): list of *bool* indicating each satellites visibility to *any* ground station - *NOTE:* must be same length as **id**
            time (:obj:`datetime`): current scenario :obj:`datetime`

        """
        for i, satellite in enumerate(self.constellation.satellites):
            next_time = self.constellation.ts.from_datetime(
                self.constellation.get_time() + 60 * self.time_status_step
            )
            satSpaceTime = satellite.at(next_time)
            subpoint = wgs84.subpoint(satSpaceTime)
            sensorRadius = compute_sensor_radius(
                subpoint.elevation.m, self.constellation.min_elevations_event[i]
            )
            self.isInRange[i], groundId = check_in_range(
                next_time, satellite, self.constellation.grounds
            )
            self.app.send_message(
                "location",
                SatelliteStatus(
                    id=i,
                    name=satellite.name,
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude=subpoint.elevation.m,
                    radius=sensorRadius,
                    commRange=self.isInRange[i],
                    time=self.constellation.get_time(),
                ).json(),
            )


# define an observer to send event detection events
class EventDetectedObserver(Observer):
    """
    *This object class inherits properties from the Observer object class from the observer template in the NOS-T tools library*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
          
    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class in NOS-T tools library*

        In this instance, the callback function checks for notification of the "detected" property and publishes :obj:`EventDetected` message to *PREFIX/constellation/detected* topic:

        """
        if property_name == "detected":
            self.app.send_message(
                "detected",
                EventDetected(
                    eventId=new_value["eventId"],
                    detected=new_value["detected"],
                    detected_by=new_value["detected_by"],
                ).json(),
            )


# define an observer to send event reporting events
class EventReportedObserver(Observer):
    """
    *This object class inherits properties from the Observer object class from the observer template in the NOS-T tools library*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
              
    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class in NOS-T tools library*

        In this instance, the callback function checks for notification of the "reported" property and publishes :obj:`EventReported` message to *PREFIX/constellation/reported* topic:

        """
        if property_name == "reported":
            self.app.send_message(
                "reported",
                EventReported(
                    eventId=new_value["eventId"],
                    reported=new_value["reported"],
                    reported_by=new_value["reported_by"],
                    reported_to=new_value["reported_to"],
                ).json(),
            )