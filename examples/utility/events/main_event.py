# -*- coding: utf-8 -*-
"""
    *This application demonstrates a simulation of a set of randomly generated scientific events
    
    The application contains a single :obj:`Environment` class which generates the random events for the simulation in a 
    :obj:`DataFrame` and listens to the time status published by the manager application and publishes event information 
    at the specified start :obj:`datetime` sunrise/sunset :obj:`datetime` and event finish :obj:`datetime`.

"""

import time
import random
import os
import sys
import logging
import datetime
from dotenv import dotenv_values
import pandas as pd
from pytz import timezone
from skyfield import almanac
from skyfield.api import N, W, wgs84, load

pd.options.mode.chained_assignment = None

from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
superparent = os.path.dirname(parent)

sys.path.append(superparent)
sys.path.append(parent)

from schemas import EventState, EventStarted, EventDetected, EventReported, EventDayChange, EventFinished
from config import PARAMETERS


logging.basicConfig(level=logging.INFO)


# define an observer to manage event updates and record to a dataframe events
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions 
        event_count (:obj:`int`): An integer specifying the number of events to be generated
        event_length (:obj:`float`): A float specifying the duration of each event in hours
        event_start_range (:obj:`tuple` of :obj:`float`): A tuple of values specifying the start and end of the range of times event start times may be in, relative to the start of the simulation in hours
        scenario_start (:obj:`datetime`): A datetime specifying the start date and time of the simulation
        scenario_length (:obj:`float`): A float specifying the length of the simulation in hours
        seed (:obj:`any`): A value specifying the seed used for pseudorandom number generation for event locations and start times
    """

    def __init__(self, app, event_count, event_length, event_start_range, scenario_start, scenario_length, seed):
        self.app = app
        self.event_count = event_count
        self.event_length = event_length
        self.event_start_range = event_start_range
        self.scenario_start = scenario_start
        self.scenario_length = scenario_length
        self.seed = seed

        self.events = self.generate_events()

    def generate_events(self):
        """
            :obj:`Environment` method to generate events with ID, start time, finish time, latitude and longitude, 
            list of sunrise/sunset times, and indicator of initial day/night status.    
        """

        # Load in timescale and Ephemeris
        ts = load.timescale()
        eph = load("de421.bsp")

        # Checks if a seed is passed when the script is ran, if not generate a random one
        random.seed(int(self.seed))

        # Creates list of IDs
        eventIds = [id for id in range(0, int(self.event_count))]

        # Initalizes event attribute lists
        eventStarts = []
        eventFinishes = []
        eventLats = []
        eventLongs = []
        eventSunriseSunsets = []
        eventIsDays = []

        # Iterates over event Ids and generates random start times and locations. Also calculates finish times and
        # relevant sunrise and sunset times for each event.
        for eventId in eventIds:

            # Create random event start time within self.event_start_range, add it to list of start times
            eventStart = self.scenario_start + datetime.timedelta(minutes=random.randrange(self.event_start_range[0]*60, self.event_start_range[1]*60))
            eventStarts.append(eventStart)

            # Calculate event finish time based on above start time and self.event_length
            eventFinishes.append(eventStart + datetime.timedelta(hours=self.event_length))

            # Generate random latitude for event, not too close to poles, and add to list of latitudes
            eventLat = random.randrange(-60, 60)
            eventLats.append(eventLat)

            # Generate random longitude for event, anywhere on the planet, and add to list of longitudes
            eventLong = random.randrange(-180, 180)
            eventLongs.append(eventLong)

            # Calculate lower bound of time range for sunrise/sunset calculation for this event, either the start time of the event
            # or the start of the scenario (some events start times may be before t=0) 
            day_change_range_start = max(
                    self.scenario_start, 
                    eventStart
                )
            
            # Calculate upper bound of time range for sunrise/sunset calculation for this event, either the end time of the event or 
            # the end of the scenario (some events end times may be after the scenario ends)
            day_change_range_end = min(
                    self.scenario_start+datetime.timedelta(hours=self.scenario_length), 
                    eventStart + datetime.timedelta(hours=self.event_length)
                )

            # Calculates all sunrise and sunset times during the 24 hours prior to the start of the event.
            # t0 is list of Skyfield Time objects, y0 is a list of 0s and 1s indicating if the corresponding time 
            # in t0 is a sunset(1) or sunrise(0), respectively.
            # NOTE: This is necessary to determine the sun state at the start of the event.
            t0, y0 = almanac.find_discrete(
                ts.from_datetime(day_change_range_start - datetime.timedelta(hours=24)),
                ts.from_datetime(day_change_range_start),
                almanac.sunrise_sunset(eph, wgs84.latlon(eventLat, eventLong)
                )
            )

            # Calculates all sunrise and sunset times during the day change range. Formatted the same as t0 and y0 above.
            t, y = almanac.find_discrete(
                ts.from_datetime(day_change_range_start),
                ts.from_datetime(day_change_range_end),
                almanac.sunrise_sunset(eph, wgs84.latlon(eventLat, eventLong)
                )
            )

            # NOTE: The above calculations utilize Skyfield's Almanac. These calcuations are extremely time intensive, and are 
            # responsible for the significant time this application takes to start.

            # Creates a list of two lists, [[the sun state change times during the event], [the most recent sun state change
            # prior to the start of the day change range + all sun state changes during the day change range]]. The second list will 
            # have a length of one more than the first.
            eventSunriseSunset = [list(t.utc_datetime()), [int(y0[-1])] + [int(num) for num in y]]

            # Assign the most recent sun change (calculated above) to the current day state and remove it from the list. The two lists 
            # in eventSunriseSunset are now the same length.
            eventIsDay = eventSunriseSunset[1].pop(0)

            # Add this events sun change data to lists
            eventIsDays.append(eventIsDay)
            eventSunriseSunsets.append(eventSunriseSunset)

        # Create DataFrame of events from the lists created in the above loop
        events = pd.DataFrame(
            data={
                "eventId": eventIds,
                "started": [False for _ in eventIds],
                "start": eventStarts,
                "finish": eventFinishes,
                "latitude": eventLats,
                "longitude": eventLongs,
                "sunriseSunset": eventSunriseSunsets,
                "isDay": eventIsDays
            }
        )

        # Index the DataFrame by eventId
        events.set_index("eventId", inplace=True)

        return events


    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks the simulation :obj:`datetime` against 
        each scheduled event start :obj:`datetime`, sunrise/sunset :obj:`datetime`, and finish 
        :obj:`datetime` for the scenario. If immediately past any of these event times, an 
        :obj:`EventStarted`,  :obj:`EventDayChange`, or :obj:`EventFinished` message
        is sent to *PREFIX/event/start*, *PREFIX/event/dayChange*, *PREFIX/event/finish*, respectively.

        """
        # Checks if the property being changed is time
        if property_name == "time":

            # Iterates over events, publish any relevant EventStarted, EventDayChange, or EventFinish messages
            for eventId, event in self.events.iterrows():
                
                # If it's past the event start time and the event hasn't already started, send EventStart message
                if event["start"] <= new_value and event["started"] == False:
                    self.events["started"][eventId] = True
                    self.app.send_message(
                        "start",
                        EventStarted(
                            eventId=eventId,
                            start=event["start"],
                            latitude=event['latitude'],
                            longitude=event['longitude'],
                            isDay=event['isDay']
                        ).json(),
                    )

                # sunriseSunset list size is inconsistent between events and locations, so try/except statement avoids invalid index 
                # errors on empty lists
                # NOTE: Could probably be implemented more cleanly
                try:
                    # if the first sunrise/sunset time is before current time, remove it from the both sunriseSunset lists
                    # and send EventDayChange message
                    if event["sunriseSunset"][0][0] <= new_value:
                        self.events["sunriseSunset"][eventId][0].pop(0)
                        self.events["isDay"][eventId] = int(self.events["sunriseSunset"][eventId][1].pop(0))

                        self.app.send_message(
                            "dayChange",
                            EventDayChange(
                                eventId=eventId,
                                isDay=self.events["isDay"][eventId]
                            ).json(),
                        )
                except:
                    pass

                # If the eventFinish time is between the current and previous times, send EventFinished message
                if event["finish"] <= new_value and event["finish"] > old_value:
                    self.app.send_message(
                        "finish",
                        EventFinished(
                            eventId=eventId
                        ).json(),
                    )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("event")

    # Create environment that generates events
    environment = Environment(app, 
        PARAMETERS['EVENT_COUNT'], 
        PARAMETERS['EVENT_LENGTH'], 
        PARAMETERS['EVENT_START_RANGE'], 
        datetime.datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=datetime.timezone.utc), 
        PARAMETERS['SCENARIO_LENGTH'],
        PARAMETERS['SEED'])

    # add the environment observer to monitor for event status events
    app.simulator.add_observer(environment)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PARAMETERS['PREFIX'],
        config,
        True,
        time_status_step=datetime.timedelta(seconds=10) * PARAMETERS['SCALE'],
        time_status_init=datetime.datetime.fromtimestamp(PARAMETERS['SCENARIO_START']).replace(tzinfo=datetime.timezone.utc),
        time_step=datetime.timedelta(seconds=0.5) * PARAMETERS['SCALE'],
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(1)