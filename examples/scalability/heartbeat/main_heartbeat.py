# -*- coding: utf-8 -*-
"""
*An application to publish messages at regular time intervals, used for NOS-T stress tests*

This application includes a :obj:`CustomHeartbeat` object class that mimics the time status messages of a managed application, but with an additional payload that includes a random string of specified length to vary the number of bytes per message and investigate it's impact on delays.

"""

import json
import logging
import random
import string
from datetime import timedelta

from heartbeat_config_files.config import MSG_LENGTH, MSG_PERIOD

from nost_tools.application_utils import ShutDownObserver, ModeStatusObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import ScenarioTimeIntervalPublisher

logging.basicConfig(level=logging.INFO)


def randStr(chars=string.ascii_uppercase + string.digits, N=10):
    return "".join(random.choice(chars) for _ in range(N))


# Using ScenarioTimeIntervalPublisher but want to customize the heartbeat message size, period, and number of instances
class CustomHeartbeat(ScenarioTimeIntervalPublisher):
    """
    Publishes time status messages at a regular interval (scenario time). The user can optionally provide a :obj:`timedelta` between time status messages and :obj:`datetime` for the initial time status message.

    Attributes:
        app (:obj:`Application`): the application that will be publishing time status messages
        msg_length (int): number of characters per message, which also matches the number of bytes per message (1 *char* = 1 byte)
        time_status_step (:obj:`timedelta`): optional duration between time status 'heartbeat' messages (defaults to 1 second)
        time_status_init (:obj:`datetime`): optional initial scenario datetime to start publishing time status 'heartbeat' messages (defaults to simulation start time dictated from the manager)
    """

    def __init__(self, app, msg_length, time_status_step=None, time_status_init=None):
        super().__init__(app, time_status_step, time_status_init)
        self.msg_length = msg_length

    def publish_message(self):
        """
        *Abstract publish_message method inherited from the ScenarioTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

        This method sends a message to the *PREFIX/status/heartbeat/time* which includes:

        Args:
            name (str): application name
            description (str): optional application description (prints empty string if nothing provided)
            simTime (:obj:`datetime`): current scenario :obj:`datetime`
            time (:obj:`datetime`): current simulator wallclock :obj:`datetime`
            addPayload (str): random string of user specified length

        """
        self.status = {
            "name": self.app.app_name,
            "description": self.app.app_description,
            "properties": {
                "simTime": str(self.app.simulator.get_time()),
                "time": str(self.app.simulator.get_wallclock_time()),
                "addPayload": randStr(N=(MSG_LENGTH - 160)),
            },
        }
        self.app.send_message(
            ".".join(["status", self.app.app_name]), "time", json.dumps(self.status)
        )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Load config
    config = ConnectionConfig(yaml_file="scalability.yaml")

    # Define the simulation parameters
    NAME = "heartbeat"

    # create the managed application
    app = ManagedApplication(NAME)

    # new heartbeat
    newBeat = CustomHeartbeat(app, MSG_LENGTH, timedelta(seconds=MSG_PERIOD))

    # add CustomHeartbeat as an observer
    app.simulator.add_observer(newBeat)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add ModeStatusObserver
    app.simulator.add_observer(ModeStatusObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
        True,
    )

    # message sent to indicate message size and periodicity
    app.send_message(
        app.app_name,
        "settings",
        json.dumps({"messageBytes": str(MSG_LENGTH), "periodicity": str(MSG_PERIOD)}),
    )
