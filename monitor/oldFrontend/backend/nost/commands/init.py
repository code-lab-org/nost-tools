#!/usr/bin/env python

import json
import re
from dateutil import parser
from datetime import datetime, timezone


def init(client, prefix, data):
    """ Initializes time range for execution.
     
    Args:
        client (object): MQTT client for publishing messages.
        prefix (str): Prefix of execution topic.
        data (object): Request body.

    Returns:
        bool: Whether the operation was successful.
        datetime.datetime: Simulation start time.
        datetime.datetime: Simulation stop time.
    """
    sim_start_time, sim_stop_time, success = "", "", True
    try:
        sim_start_time = parser.parse(
            data["simStartTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print("\nError: Malformed ISO-8601 datetime or missing string: 'simStartTime'\n")
        success = False
    try:
        sim_stop_time = parser.parse(
            data["simStopTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print("\nError: Malformed ISO-8601 datetime or missing string: 'simStopTime'\n")
        success = False
    # Publish message
    if success:
        response = client.publish(
            f"{prefix}/manager/init",
            json.dumps({
                "taskingParameters": {
                    "simStartTime": sim_start_time.isoformat(),
                    "simStopTime": sim_stop_time.isoformat()
                }
            })
        )
        response.wait_for_publish()
    return (success, sim_start_time, sim_stop_time)
