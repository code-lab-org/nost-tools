#!/usr/bin/env python

import json
import re
from dateutil import parser
from datetime import datetime, timezone


def stop(sim, client, prefix, data):
    """ Stops the execution.
     
    Args:
        sim (sim.simulator.Simulator): Simulator class for prefix.
        client (object): MQTT client for publishing messages.
        prefix (str): Prefix of execution topic.
        data (object): Request body.

    Returns:
        bool: Whether the operation was successful.
        datetime.datetime: Simulation start time.
        datetime.datetime: Simulation stop time.
    """
    sim_stop_time, success = "", True
    try:
        sim_stop_time = parser.parse(
            data["simStopTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print("\nError: Malformed ISO-8601 datetime or missing string: 'simStopTime'\n")
        success = False

    # Update simulator
    if success:
        sim.set_end_time(sim_stop_time)
        print('\nSimulation stopping at {:}\n'.format(
            sim_stop_time.isoformat()))

        # Publish message
        response = client.publish(
            f"{prefix}/manager/stop",
            json.dumps({
                "taskingParameters": {
                    "simStopTime": sim_stop_time.isoformat()
                }
            })
        )
        response.wait_for_publish()

    return success
