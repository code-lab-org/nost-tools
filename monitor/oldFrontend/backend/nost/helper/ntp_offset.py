#!/usr/bin/env python

import json
from datetime import datetime, timedelta, timezone
import ntplib
import time


def get_wallclock_offset(last_nist_query):
    """ Contacts NTP server (atomic clock) to synchronize internal time with offset.

    Args:
        last_nist_query (datetime.datetime): most recent NTP request.

    Returns:
        datetime.timedelta: Offset from NTP server.
        datetime.datetime: Time of last NTP request.
    """
    offset = None
    nist_delay = 4
    while offset is None:
        if last_nist_query is not None:
            time_to_wait = timedelta(seconds=nist_delay) - \
                (datetime.now(tz=timezone.utc) - last_nist_query)
            if time_to_wait > timedelta(seconds=0):
                print('Waiting for {} to issue NIST query'.format(time_to_wait))
                time.sleep(time_to_wait/timedelta(seconds=1))
        try:
            print("Contacting NTP servers to retrieve wallclock offset")
            response = ntplib.NTPClient().request(
                'pool.ntp.org', version=3, timeout=5)
            offset = response.offset
            print("Wallclock offset is set to " + str(offset) + " seconds")
            return (timedelta(seconds=offset), datetime.now(tz=timezone.utc))
        except ntplib.NTPException:
            print("Could not connect to NTP servers, trying again in " +
                  str(nist_delay) + " seconds")
            last_nist_query = datetime.now(tz=timezone.utc)
