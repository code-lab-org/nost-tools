from nost_tools.simulator import Simulator, Mode
from datetime import datetime, timedelta, timezone
import time
import logging
import threading

logger = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

s = Simulator()

start = datetime.now()

s.initialize(start, time_scale_factor=1)
# s.execute(datetime.now(), timedelta(seconds=20), timedelta(seconds=1), time_scale_factor=1)

exec_thread = threading.Thread(
    target=s.execute,
    kwargs={
        "init_time": start,
        "duration": timedelta(seconds=10),
        "time_step": timedelta(seconds=1),
        "time_scale_factor": 1,
    },
)
exec_thread.start()

time.sleep(3)
s.pause()
time.sleep(5)
s.resume()

# class TimeScaleUpdate(object):
#     def __init__(self, time_scale_factor: float, update_time: datetime, is_simulation_time=True):
#         self.time_scale_factor = time_scale_factor
#         self.update_time = update_time
#         self.is_simulation_time = is_simulation_time

# # Wait for simulation to start executing
# while s.get_mode() != Mode.EXECUTING:
#     time.sleep(0.001)

# utc_now = datetime.now(timezone.utc)

# time_scale_updates = [
#     TimeScaleUpdate(0, utc_now + timedelta(seconds=5), False),
#     TimeScaleUpdate(1, utc_now + timedelta(seconds=10), False)
# ]
# command_lead = timedelta(0)

# # Process time scale updates
# for update in time_scale_updates:
#     update_time = s.get_wallclock_time_at_simulation_time(
#         update.update_time
#     ) if update.is_simulation_time else update.update_time
#     # Sleep until update time using heartbeat-safe approach
#     sleep_seconds = max(
#         0,
#         (
#             (update_time - s.get_wallclock_time())
#             - command_lead
#         )
#         / timedelta(seconds=1),
#     )

#     # Use our heartbeat-safe sleep
#     if sleep_seconds > 0:
#         # Sleep in smaller chunks to allow heartbeats to pass through
#         check_interval = 30  # Check every 30 seconds at most
#         end_time = time.time() + sleep_seconds

#         logger.debug(f"Starting heartbeat-safe sleep for {sleep_seconds:.2f} seconds")

#         while time.time() < end_time:
#             # Calculate remaining time
#             remaining = end_time - time.time()

#             # Sleep for the shorter of check_interval or remaining time
#             sleep_time = min(check_interval, remaining)

#             if sleep_time > 0:
#                 time.sleep(sleep_time)
#                 logger.debug(
#                     f"Heartbeat check: {remaining:.2f} seconds remaining in sleep"
#                 )

#     # Issue the update command
#     s.set_time_scale_factor(update.time_scale_factor, s.get_time())

#     # Wait until update takes effect
#     while s.get_time_scale_factor() != update.time_scale_factor:
#         time.sleep(0.001)
