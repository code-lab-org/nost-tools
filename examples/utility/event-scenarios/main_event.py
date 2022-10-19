# -*- coding: utf-8 -*-
"""
    *This application demonstrates a simulation of a schedule of fires given geospatial locations and specified datetimes (at one minute resolution)*
    
    The application contains a single :obj:`Environment` class which listens to the time status published by the manager application and publishes fire information at the specified ignition :obj:`datetime`. The application also contains callback messages that updates :obj:`datetime` in the fires :obj:`DataFrame` for each of ignition (including latitude-longitude :obj:`GeographicPosition`), detection, and reporting.

"""

from random import randint, randrange, seed
import sys
import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
import pandas as pd

pd.options.mode.chained_assignment = None

import importlib.resources

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication

from event_config_files.schemas import EventState, EventStarted, EventDetected, EventReported
from event_config_files.config import PREFIX, SCALE, EVENT_COUNT

logging.basicConfig(level=logging.INFO)

# define an observer to manage event updates and record to a dataframe events
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        events (:obj:`DataFrame`): Dataframe of scenario scheduled events including eventId (*int*), event ignition (:obj:`datetime`), and fire latitude-longitude location (:obj:`GeographicPosition`)
    """

    def __init__(self, app, events):
        self.app = app
        self.events = events

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks the simulation :obj:`datetime` against each scheduled event ignition :obj:`datetime` for the scenario. If past the scheduled start of an event, a :obj:`EventStarted` message is sent to *PREFIX/event/location*:

        .. literalinclude:: /../../utility/event-scenarios/main_event.py
            :lines: 51-66

        """
        if property_name == "time":
            
            new_events = self.events[
                (self.events.start <= new_value) & (self.events.start > old_value)
            ]
            print(f"cum: {new_events}")
            for index, event in new_events.iterrows():
                # print(f"eventId: {event.eventId}")
                self.app.send_message(
                    "location",
                    EventStarted(
                        eventId=event.eventId,
                        start=event.start,
                        latitude=event.latitude,
                        longitude=event.longitude,
                    ).json(),
                )

    def on_event(self, client, userdata, message):
        start = EventStarted.parse_raw(message.payload)
        for key, event in self.events.iterrows():
            if key == start.eventId:
                self.events["eventState"][key] = EventState.started
                break

    def on_detected(self, client, userdata, message):
        detect = EventDetected.parse_raw(message.payload)
        for key, event in self.events.iterrows():
            if key == detect.eventId:
                self.events["eventState"][key] = EventState.detected
                self.events["detected"][key] = detect.detected
                self.events["detected_by"][key] = detect.detected_by
                break

    def on_reported(self, client, userdata, message):
        report = EventReported.parse_raw(message.payload)
        for key, event in self.events.iterrows():
            if key == report.eventId:
                self.events["eventState"][key] = EventState.reported
                self.events["reported"][key] = report.reported
                self.events["reported_by"][key] = report.reported_by
                self.events["reported_to"][key] = report.reported_to
                break


def on_event(client, userdata, message):
    """
    *Callback function parses a EventStarted message and switches EventState from "undefined" to "started"*

    .. literalinclude:: /../../utility/event-scenarios/main_event.py
        :lines: 68-73

    """
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_event(client, userdata, message)


def on_detected(client, userdata, message):
    """
    *Callback function parses a EventDetected message, switches EventState from "started" to "detected", and records time of first detection and name of satellite detecting the fire*

    .. literalinclude:: /../../utility/eventscenarios/main_event.py
        :lines: 75-82

    """
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_detected(client, userdata, message)


def on_reported(client, userdata, message):
    """
    *Callback function parses a EventReported message, switches EventState from "detected" to "reported", and records time of first report, name of satellite reporting the fire, and groundId receiving the report*

    .. literalinclude:: /../../utility/event-scenarios/main_event.py
        :lines: 84-92

    """
    for index, observer in enumerate(app.simulator._observers):
        if isinstance(observer, Environment):
            app.simulator._observers[index].on_reported(client, userdata, message)


if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("event")

    if (len(sys.argv) == 0):
        seed(randint(0, 10000000000))
    else:
        seed(sys.argv[0])

    eventIds = [id for id in range(0, EVENT_COUNT)]

    eventStarts = []
    eventLats = []
    eventLongs = []
    for event in range(0, EVENT_COUNT):
        eventStarts.append(datetime(2022, 10, 3, 7, 20, 0, tzinfo=timezone.utc) + timedelta(minutes=randrange(0, 3*1440)))
        eventLats.append(randrange(-90, 90))
        eventLongs.append(randrange(-180, 180))

    # Read the csv file and convert to a DataFrame with initial column defining the index
    events = pd.DataFrame(
        data={
            "eventId": eventIds,
            "start": eventStarts,
            "latitude": eventLats,
            "longitude": eventLongs,
        }
    )
    print(events)

    # Add blank columns to data frame for logging state, detection time, reporting time, and detector satellite
    events.insert(1, "eventState", EventState.undefined)
    events.insert(3, "detected", datetime(1900, 1, 1, tzinfo=timezone.utc))
    events.insert(4, "detected_by", "Undetected")
    events.insert(5, "reported", datetime(1900, 1, 1, tzinfo=timezone.utc))
    events.insert(6, "reported_by", "Unreported")
    events.insert(7, "reported_to", None)

    # add the environment observer to monitor for event status events
    app.simulator.add_observer(Environment(app, events))

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2022, 10, 3, 7, 20, 0, tzinfo=timezone.utc),
        time_step=timedelta(seconds=2) * SCALE,
    )

    # add message callbacks for event ignition, detection, and report
    app.add_message_callback("event", "location", on_event)
    app.add_message_callback("constellation", "detected", on_detected)
    app.add_message_callback("constellation", "reported", on_reported)

    while True:
        pass