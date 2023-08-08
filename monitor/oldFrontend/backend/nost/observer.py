#!/usr/bin/env python

from nost.commands import update, stop
from nost.config import HEADER

import json
from dateutil import parser
from datetime import datetime, timedelta, timezone


class Observer(object):
    """ This is the abstract observer class. """

    def on_change(self, source, property_name, old_value, new_value):
        """ Called on property change. """
        pass


class Observable(object):
    """ This is the base observable class. """

    def __init__(self):
        """ Constructor method. """
        # list of observers to be notified of events
        self._observers = []

    def add_observer(self, observer):
        """ Adds an observer. """
        self._observers.append(observer)

    def remove_observer(self, observer):
        """ Removes an observer. """
        return self._observers.remove(observer)

    def clear_observers(self):
        """ Clears observers. """
        self._observers = []

    def notify_observers(self, property_name, old_value, new_value):
        """ Notifies observers of a property change. """
        if old_value != new_value:
            for observer in self._observers:
                observer.on_change(self, property_name, old_value, new_value)


class PublishObserver(Observer):
    """ This is the PublishObserver class which implements the abstract Observer class.

    This class publishes time status messages at a interval defined during instantion and is removed after an execution completes.
    Publishes messages to "{prefix}-manager/time"

    Args:
        client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        prefix (str): Prefix of specified execution.

    Attributes:
        _client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        _prefix (str): Prefix of specified execution.
        _internal_step (datetime.timedelta): Execution time between published messages.
        _next_time (datetime.datetime): Time of next message to publish.
    """

    def __init__(self, client, prefix):
        """ Constructor method. """
        self._client = client
        self._prefix = prefix
        self._internal_step = timedelta(seconds=1)
        self._next_time = None

    def send_message(self, source):
        message = {
            **HEADER,
            'properties': {
                'simTime': source.get_time().isoformat(),
                'time': source.get_wallclock_time().isoformat(),
                'timeScalingFactor': source.get_time_scale_factor()
            }
        }

        self._client.publish(f"{self._prefix}-manager/time",
                             payload=json.dumps(message))

    def on_change(self, source, property_name, old_value, new_value):
        """ Publishes time Messages """
        if property_name == "time":
            if self._next_time is None:
                self.send_message(source)
                self._next_time = source.get_wallclock_time() + self._internal_step
            elif source.get_wallclock_time() > self._next_time:
                self.send_message(source)
                self._next_time += self._internal_step
        if property_name == "mode" and str(new_value) == "Mode.TERMINATING":
            self.send_message(source)


class ExternalPublishObserver(Observer):
    """ This is the ExternalPublishObserver class which implements the abstract Observer class. 

    This class publishes time status messages at a interval defined during instantion and is removed after an execution completes.
    Publishes messages to "{prefix}/manager/time"

    Args:
        client (paho.mqtt.client.Client):  Access to the MQTT client for publishing messages.
        topic (str): Topic to publish messages to.
        publish_step (datetime.timedelta): Execution time between published messages.
        publish_start_time (datetime.datetime): Specifies when to start publishing messages in execution time, defaults to None which will use simStartTime.

    Attributes:
        _client (paho.mqtt.client.Client):  Access to the MQTT client for publishing messages.
        _topic (str): Topic to publish messages to.
        _publish_step (datetime.timedelta): Execution time between published messages.
        _next_publish_time (datetime.datetime): Specifies when to publish next message.
    """

    def __init__(self, client, topic, publish_step, publish_start_time=None):
        """ Contructor method. """
        self._client = client
        self._topic = topic
        self._publish_step = publish_step
        self._next_publish_time = publish_start_time

    def on_change(self, source, property_name, old_value, new_value):
        """ Publishes nost/time Messages """
        if property_name == "time":
            if self._next_publish_time is None:
                self._next_publish_time = source.get_init_time()
            while new_value + source.get_time_step() > self._next_publish_time:
                message = {
                    **HEADER,
                    'properties': {
                        'simTime': self._next_publish_time.isoformat(),
                        'time': source.get_wallclock_time().isoformat()
                    }
                }
                self._client.publish(self._topic, payload=json.dumps(message))
                self._next_publish_time += self._publish_step


class TestScriptObserver(Observer):
    """ This is the TestScriptObserver class which implements the abstract Observer class. 

    This class executes time status updates predefined by a test script.

    Args:
        sim (nost.simulator.Simulator): Simulator class to execute commands directly to execution state.   
        client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        prefix (str): Prefix of specified execution.
        test_script_data (list): State updates over the execution.

    Attributes:
        _sim (nost.simulator.Simulator): Simulator class to execute commands directly to execution state.   
        _client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        _prefix (str): Prefix of specified execution.
        _data (list): State updates over the execution.
        _length (int): Amount of state updates.
        _index (int): Index of next state update.
        _next_time (datetime.datetime): Time of next state update.
    """

    def __init__(self, sim, client, prefix, test_script_data):
        """ Constructor method. """
        self._sim = sim
        self._client = client
        self._prefix = prefix
        self._data = test_script_data
        self._length = len(test_script_data)
        self._index = 0
        self._next_time = None

    def set_next_time(self, data):
        """ Sets next time to execute update. """
        if data['type'] == 'update':
            self._next_time = parser.parse(
                data['properties']['simUpdateTime']).replace(tzinfo=timezone.utc)
        elif data['type'] == 'stop':
            self._next_time = parser.parse(
                data['properties']['simStopTime']).replace(tzinfo=timezone.utc)

    def on_change(self, source, property_name, old_value, new_value):
        """ On change function observing execution time to issue time-based updates. """
        if property_name == "time":
            if self._next_time is None and self._length != 0:
                self.set_next_time(self._data[0])
            while self._next_time is not None and new_value + source.get_time_step() > self._next_time:
                if self._data[self._index]['type'] == "update":
                    update.update(self._sim, self._client, self._prefix,
                                  self._data[self._index]['properties'])
                elif self._data[self._index]['type'] == "stop":
                    stop.stop(self._sim, self._client, self._prefix,
                              self._data[self._index]['properties'])
                if self._index + 1 < self._length:
                    self._index += 1
                    self.set_next_time(self._data[self._index])
                else:
                    self._next_time = None
                    self._length = 0


class StopMessageObserver(Observer):
    """ This is the StopMessageObserver class which implements the abstract Observer class. 

    This class publishes a stop message when the execution terminates.

    Args:
        client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        prefix (str): Prefix of specified execution.

    Attributes:
        _client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        _prefix (str): Prefix of specified execution.
    """

    def __init__(self, client, prefix):
        self._client = client
        self._prefix = prefix

    def on_change(self, source, property_name, old_value, new_value):
        if property_name == "mode" and str(new_value) == "Mode.TERMINATING":
            message = {
                **HEADER,
                'properties': {
                    'stopTime': source.get_time().isoformat()
                }
            }

            self._client.publish(
                f"{self._prefix}/manager/stopped", payload=json.dumps(message))


class ModeMessageObserver(Observer):
    """ This is the ModeMessageObserver class which implements the abstract Observer class. 

    This class publishes mode status updates of the simulator class.

    Args:
        client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        prefix (str): Prefix of specified execution.

    Attributes:
        _client (paho.mqtt.client.Client): Access to the MQTT client for publishing messages.
        _prefix (str): Prefix of specified execution.
    """

    def __init__(self, client, prefix):
        self._client = client
        self._prefix = prefix

    def on_change(self, source, property_name, old_value, new_value):
        if property_name == "mode":
            message = {
                **HEADER,
                'properties': {
                    'mode': str(new_value)[5:]
                }
            }

            self._client.publish(
                f"{self._prefix}/manager/mode", payload=json.dumps(message))
