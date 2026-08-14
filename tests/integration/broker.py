"""
Support for tests that run against a real RabbitMQ broker.

The unit tests substitute pika's client objects, which makes them fast and lets
them assert things a broker cannot observe, such as which thread called
basic_publish. What they cannot check is that the library talks to RabbitMQ
correctly: exchange declaration, routing, and end-to-end delivery. These tests
cover that gap.

They are skipped when no broker is reachable, so `pytest` stays green on a machine
without one. To run them, start the broker documented in the operator's guide:

    docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 \\
      -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=admin \\
      rabbitmq:3.13-management
"""

import os
import socket
import tempfile
import unittest

BROKER_HOST = os.environ.get("NOST_TEST_BROKER_HOST", "localhost")
BROKER_PORT = int(os.environ.get("NOST_TEST_BROKER_PORT", "5672"))
BROKER_USER = os.environ.get("NOST_TEST_BROKER_USER", "admin")
BROKER_PASSWORD = os.environ.get("NOST_TEST_BROKER_PASSWORD", "admin")

YAML_TEMPLATE = """
info:
  title: Integration test configuration
  version: '1.0.0'
  description: Points at a local broker for end-to-end tests
servers:
  rabbitmq:
    keycloak_authentication: False
    host: "{host}"
    port: {port}
    tls: False
    virtual_host: "/"
    heartbeat: 60
    connection_attempts: 2
    retry_delay: 1
execution:
  general:
    prefix: {prefix}
"""


SCENARIO_YAML_TEMPLATE = """
info:
  title: Integration test scenario configuration
  version: '1.0.0'
  description: A short scenario the manager can drive end to end
servers:
  rabbitmq:
    keycloak_authentication: False
    host: "{host}"
    port: {port}
    tls: False
    virtual_host: "/"
    heartbeat: 60
    connection_attempts: 2
    retry_delay: 1
execution:
  general:
    prefix: {prefix}
  manager:
    sim_start_time: "2020-01-01T00:00:00+00:00"
    sim_stop_time: "2020-01-01T00:01:00+00:00"
    start_time:
    time_step: "0:00:01"
    time_scale_factor: {time_scale_factor}
    time_status_step: "0:00:10"
    is_scenario_time_status_step: False
    command_lead: "0:00:01"
    required_apps:
      - manager
      - {app_name}
    init_retry_delay_s: 2
    init_max_retry: 5
    set_offset: False
    shut_down_when_terminated: False
  managed_applications:
    {app_name}:
      time_scale_factor: {time_scale_factor}
      time_step: "0:00:01"
      is_scenario_time_step: False
      set_offset: False
      time_status_step: "0:00:10"
      is_scenario_time_status_step: False
      shut_down_when_terminated: False
      manager_app_name: "manager"
"""


def write_scenario_config(prefix, app_name, time_scale_factor=60):
    """
    Writes a YAML configuration describing a one-minute scenario.

    At the default scale factor the run takes about a second of wallclock time,
    so a test can drive a complete test plan without waiting out a scenario.
    """
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    handle.write(
        SCENARIO_YAML_TEMPLATE.format(
            host=BROKER_HOST,
            port=BROKER_PORT,
            prefix=prefix,
            app_name=app_name,
            time_scale_factor=time_scale_factor,
        )
    )
    handle.close()
    return handle.name


def broker_available():
    """True when a TCP connection to the configured broker succeeds."""
    probe = socket.socket()
    probe.settimeout(2)
    try:
        probe.connect((BROKER_HOST, BROKER_PORT))
        return True
    except OSError:
        return False
    finally:
        probe.close()


requires_broker = unittest.skipUnless(
    broker_available(),
    f"no RabbitMQ broker reachable at {BROKER_HOST}:{BROKER_PORT}",
)


def write_config(prefix):
    """Writes a YAML config for the local broker and returns its path."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    handle.write(
        YAML_TEMPLATE.format(host=BROKER_HOST, port=BROKER_PORT, prefix=prefix)
    )
    handle.close()
    return handle.name


def set_broker_credentials():
    """
    Exports the broker credentials ConnectionConfig reads from the environment.

    Returns the previous values so a test can restore them.
    """
    previous = {key: os.environ.get(key) for key in ("USERNAME", "PASSWORD")}
    os.environ["USERNAME"] = BROKER_USER
    os.environ["PASSWORD"] = BROKER_PASSWORD
    return previous


def restore_environment(previous):
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
