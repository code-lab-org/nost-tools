#!/usr/bin/env python

import json
import re
from dateutil import parser
from datetime import datetime, timedelta, timezone


def update(sim, client, prefix, data):
    """ Updates the execution.
     
    Args:
        sim (sim.simulator.Simulator): Simulator class for prefix.
        client (object): MQTT client for publishing messages.
        prefix (str): Prefix of execution topic.
        data (object): Request body.

    Returns:
        bool: Whether the operation was successful.
    """

    sim_update_time, time_scaling_factor, success = "", "", True
    try:
        sim_update_time = parser.parse(
            data["simUpdateTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print("\nError: Malformed ISO-8601 datetime or missing string: 'simUpdateTime'\n")
        success = False
    try:
        time_scaling_factor = float(data["timeScalingFactor"])
    except Exception as e:
        print("\nError: Malformed floating-point or missing string: 'timeScalingFactor'\n")
        success = False

    # Update Simulator
    if success:
        sim.set_time_scale_factor(
            time_scale_factor=time_scaling_factor,
            simulation_epoch=sim_update_time
        )
        print('\nSimulation updating at {:}\n'.format(
            sim_update_time.isoformat()))
        # Publish Message
        response = client.publish(
            f"{prefix}/manager/update",
            json.dumps({
                "taskingParameters": {
                    "simUpdateTime": sim_update_time.isoformat(),
                    "timeScalingFactor": time_scaling_factor
                }
            })
        )
        response.wait_for_publish()

    return success
