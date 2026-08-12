"""
Shared test support: broker doubles and bounded wait helpers.

Deferring callbacks rather than running them is what distinguishes scheduling a
publish from performing it inline, which the thread-safe publishing path depends
on. Tests drain the recorded callbacks explicitly via run_pending().
"""

import threading
import time

import pika


def wait_for_mode(test, simulator, mode, timeout=15):
    """
    Blocks until the simulator reaches a mode, failing the test if it never does.

    Waiting in an unbounded loop turns a stalled simulator into a hung test, which
    surfaces as a job timeout with no diagnostic rather than a failure.
    """
    deadline = time.monotonic() + timeout
    while simulator.get_mode() != mode:
        if time.monotonic() > deadline:
            test.fail(
                f"simulator did not reach {mode} within {timeout}s "
                f"(mode is {simulator.get_mode()})"
            )
        time.sleep(0.05)


def wait_for(test, predicate, description, timeout=15):
    """Blocks until predicate() is true, failing the test if it never becomes true."""
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            test.fail(f"timed out after {timeout}s waiting for {description}")
        time.sleep(0.05)


class FakeChannel:
    """Records basic_publish calls and the thread each was made from."""

    def __init__(self, fail=False):
        self.published = []
        self.publish_threads = []
        self.fail = fail
        self.is_closing = False
        self.is_closed = False

    def basic_publish(self, exchange, routing_key, body, properties=None):
        self.publish_threads.append(threading.current_thread())
        if self.fail:
            raise RuntimeError("simulated publish failure")
        self.published.append((exchange, routing_key, body))

    def routing_keys(self):
        """Routing keys published so far, in order."""
        return [routing_key for _, routing_key, _ in self.published]

    def bodies(self):
        """Message bodies published so far, in order."""
        return [body for _, _, body in self.published]


class FakeIOLoop:
    """Records callbacks instead of running them."""

    def __init__(self):
        self.callbacks = []

    def add_callback_threadsafe(self, callback):
        self.callbacks.append(callback)

    def call_later(self, _delay, callback):
        self.callbacks.append(callback)

    def run_pending(self):
        """Runs recorded callbacks in order, as pika's IO loop would."""
        pending, self.callbacks = self.callbacks, []
        for callback in pending:
            callback()
        return len(pending)


class FakeConnection:
    def __init__(self):
        self.ioloop = FakeIOLoop()
        self.is_closed = False


def wire_broker(app, prefix="test", connected=True, queue_max_size=100,
                failing_channel=False):
    """
    Attaches broker doubles to an already-constructed application.

    Bypasses start_up(), which would open a real connection, while leaving the
    publishing and queueing paths intact.
    """
    app.prefix = prefix
    app.channel = FakeChannel(fail=failing_channel)
    app.connection = FakeConnection()
    app._queue_max_size = queue_max_size
    # Avoids needing a full YAML configuration tree for publishing
    app._build_basic_properties = lambda: pika.BasicProperties()
    if connected:
        app._is_connected.set()
    else:
        app._is_connected.clear()
    return app
