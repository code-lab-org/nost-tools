"""
Shared test support: broker doubles and bounded wait helpers.

Deferring callbacks rather than running them is what distinguishes scheduling a
publish from performing it inline, which the thread-safe publishing path depends
on. Tests drain the recorded callbacks explicitly via run_pending().
"""

import threading
import time
from datetime import datetime, timedelta, timezone

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

    def __init__(self, fail=False, fail_ops=()):
        self.published = []
        self.publish_threads = []
        self.fail = fail
        # Queue operations that should raise, by name: "purge", "unbind", "delete"
        self.fail_ops = set(fail_ops)
        self.is_closing = False
        self.is_closed = False
        # Queue administration performed during teardown, in order
        self.operations = []

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

    # Queue administration. A real broker answers these asynchronously and pika
    # runs the callback on the IO thread; running it inline is the deterministic
    # equivalent, and keeps the completion signalling under test rather than the
    # scheduling.

    def _run(self, op, queue, callback, **detail):
        self.operations.append((op, queue, detail))
        if op in self.fail_ops:
            raise RuntimeError(f"simulated {op} failure")
        if callback is not None:
            callback(None)

    def queue_purge(self, queue, callback=None):
        self._run("purge", queue, callback)

    def queue_unbind(self, queue, exchange=None, routing_key=None, callback=None):
        self._run("unbind", queue, callback, exchange=exchange)

    def queue_delete(self, queue, if_unused=False, if_empty=False, callback=None):
        self._run("delete", queue, callback)

    def ops(self, op):
        """Queues an operation was performed on, in order."""
        return [queue for name, queue, _ in self.operations if name == op]


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


def wire_broker(
    app, prefix="test", connected=True, queue_max_size=100, failing_channel=False
):
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


class FakeSimulator:
    """
    Stands in for a Simulator with a clock the test controls.

    The manager waits on wallclock time and on mode transitions, both of which
    are driven by a real simulator executing in another thread. Controlling them
    directly lets a test assert command sequencing without waiting out a scenario.
    """

    def __init__(
        self, wallclock_time=None, mode=None, scenario_time=None, frozen=False
    ):
        from nost_tools.simulator import Mode

        self._wallclock_base = wallclock_time or datetime(
            2020, 1, 1, tzinfo=timezone.utc
        )
        self._monotonic_base = time.monotonic()
        # A live clock by default, so the manager's timed waits terminate as they
        # would against a real simulator. Freeze it for tests that need the
        # wallclock to hold still.
        self.frozen = frozen
        self.mode = mode or Mode.UNDEFINED
        self.time = scenario_time or datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.end_time = None
        self.time_scale_factor = 1.0
        # Scenario time is anchored to wallclock time by a fixed pair of epochs,
        # as in the real simulator. Mapping from the live wallclock instead would
        # make a future scenario time recede as fast as the clock advances, so no
        # wait on it could ever finish.
        self.wallclock_epoch = self._wallclock_base
        self.simulation_epoch = self.time
        # Recorded calls, so a test can assert what the manager asked of it
        self.set_end_time_calls = []
        self.set_time_scale_factor_calls = []
        self.pause_calls = 0
        self.resume_calls = 0
        self.observers = []

    # Clock and state, read by the manager while orchestrating

    @property
    def wallclock_time(self):
        if self.frozen:
            return self._wallclock_base
        elapsed = time.monotonic() - self._monotonic_base
        return self._wallclock_base + timedelta(seconds=elapsed)

    @wallclock_time.setter
    def wallclock_time(self, value):
        self._wallclock_base = value
        self._monotonic_base = time.monotonic()

    def get_wallclock_time(self):
        return self.wallclock_time

    def get_time(self):
        return self.time

    def get_mode(self):
        return self.mode

    def get_end_time(self):
        return self.end_time

    def get_time_scale_factor(self):
        return self.time_scale_factor

    def get_wallclock_time_at_simulation_time(self, simulation_time):
        """Maps scenario time to wallclock time against the fixed epoch pair."""
        elapsed = (simulation_time - self.simulation_epoch) / self.time_scale_factor
        return self.wallclock_epoch + elapsed

    # Commands issued by the manager

    def set_end_time(self, end_time):
        self.set_end_time_calls.append(end_time)
        self.end_time = end_time

    def set_time_scale_factor(self, factor, simulation_epoch=None):
        self.set_time_scale_factor_calls.append((factor, simulation_epoch))
        self.time_scale_factor = factor

    def pause(self):
        """Pauses immediately. A real simulator passes through PAUSING first,
        and the manager polls for PAUSED before anchoring the resume time."""
        from nost_tools.simulator import Mode

        self.pause_calls += 1
        self.mode = Mode.PAUSED

    def resume(self):
        from nost_tools.simulator import Mode

        self.resume_calls += 1
        self.mode = Mode.EXECUTING

    def add_observer(self, observer):
        self.observers.append(observer)

    # Test controls

    def advance(self, seconds):
        """Moves the wallclock forward without waiting."""
        self._wallclock_base = self.wallclock_time + timedelta(seconds=seconds)
        self._monotonic_base = time.monotonic()
