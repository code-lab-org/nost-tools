.. _timeManagement:

Time Management
===============

When developing a scenario for executing on the NOS testbed, it is crucial to understand how the applications in 
the scenario will interact with time. Will the applications rely on real-time progression? Will time be scaled up to run simulations faster than real time?
This section will detail the methods of time management for a variety of user scenarios, including selection metrics, management best practices, and code templates. 

Real Time
---------

One choice for managing time with NOS-T is to simply run applications in real time. In a real-time scenario, the applications iterate in line with the actual progression of time. Applications that may benefit from a real-time progression 
would be applications relying on external data, for example in-situ sensors, or those that want to propagate current satellite orbits. While there are many ways to manage time across a distributed network

Scaled Time
-----------

NOS-T Manager Timing Parameters 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For both of the commonly used time management techniques, the NOS-T Tools library has all controls needed to manage a user defined scenario.

To define the time parameters of a scenario, best practices encourange drafting a test plan modelled after the parameters defined by the manager tool. 

The variables that comprise the test plan are passed into the manager application upon execution. By defining these variables, a user can better understand the management of their scenario, and ensure that the goals of the project are met. 

.. code-block:: python3

    def execute_test_plan(
        self,
        sim_start_time: datetime,
        sim_stop_time: datetime,
        start_time: datetime = None,
        time_step: timedelta = timedelta(seconds=1),
        time_scale_factor: float = 1.0,
        time_scale_updates: List[TimeScaleUpdate] = [],
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        command_lead: timedelta = timedelta(seconds=0),
        required_apps: List[str] = [],
        init_retry_delay_s: int = 5,
        init_max_retry: int = 5,


.. list-table:: Variable definitions
   :widths: 50 50
   :header-rows: 1

   * - Variable
     - Explanation
   * - self
     - Reference to the manager object instanciated by the calling of the 'execute_test_plan' function
   * - sim_start_time
     - The time in 'datetime' at which the simulation should start. If a time in the past, the simulation will start immidieately. Otherwise, the simulation will begin at the specified time.
   * - sim_stop_time
     - The time in 'datetime' at which the simulation will stop.
   * - time_step
     - The iteration of time per the tick/tock methods. The standard in 1 second, that is then scaled through the time_scale_factor.
   * - time_scale_factor
     - A multiplication factor that scales the time step of a function. For example, a factor of 60  mean that one second of real time is 60 seconds (one minute) of simulation time. This factor can be used in non-real-time scenarios to progress through long periods of time quickly.e
   * - time_scale_updates
     - This variable is an optional list of timestamps, at which the scale factor can be updated to a specified amount. This is used to 'fast-forward' through parts of the simulation, or slow down for further analysis.
   * - time_status_step
     - This is the interval at which the time of the application will be published, an important step for checking consistency and debugging.
   * - time_status_init
     - This is the first timestamp at which status will be published
   * - command_lead
     - This variable sends a command offset that delays execution of the test plan by the specified time.
   * - required_apps
     - This optional variable allows the user to specifiy applications required to be connected for execution.
   * - init_retry_delay_s
     - This variable defines the delay from last execution of the test plan in the event of failure.
   * - init_max_retry
     - This variable sets the retry limit for a test plan



The Tick and Tock Methods
^^^^^^^^^^^^^^^^^^^^^^^^^

In these cases, it is best practice for a user to utilize all features of the manager, and the tick/tock methods.
Below are snippets for the tick/tock methods, but their full integration can be found in the :ref:`FireSat+ tutorial <tutorialConstellation>`.


.. code-block:: python3

    def tick(self, time_step):
        super().tick(time_step)
        self.next_positions = [
            wgs84.subpoint(
                satellite.at(self.ts.from_datetime(self.get_time() + time_step))
            )
            for satellite in self.satellites
        ]
        for i, satellite in enumerate(self.satellites):
            then = self.ts.from_datetime(self.get_time() + time_step)
            self.min_elevations_fire[i] = compute_min_elevation(
                float(self.next_positions[i].elevation.m), FIELD_OF_REGARD[i]
            )
            for j, fire in enumerate(self.fires):
                if self.detect[j][self.names[i]] is None:
                    topos = wgs84.latlon(fire["latitude"], fire["longitude"])
                    isInView = check_in_view(
                        then, satellite, topos, self.min_elevations_fire[i]
                    )
        ...

The 'tick' method progresses the application internal time using the 'time_step' variable which is explored more in the next section, and the following 'tock' method progresses
the state of the application (location, field of regard, elevation angle, etc.). 

.. code-block:: python3

    def tock(self):
        self.positions = self.next_positions
        for i, newly_detected_fire in enumerate(self.detect):
            if newly_detected_fire["firstDetect"]:
                detector = newly_detected_fire["firstDetector"]
                self.notify_observers(
                    self.PROPERTY_FIRE_DETECTED,
                    None,
                    {
                        "fireId": newly_detected_fire["fireId"],
                        "detected": newly_detected_fire[detector],
                        "detected_by": detector,
                    },
                )
                self.detect[i]["firstDetect"] = False
        ...




Time Synchronization
--------------------

One such method is used in the provided examples -- iteration functions that operate in parallel to wallclock requests. The National Institute of Standards and Technology (NIST) offers a pooled service that allows 
a user to standardize their computer's internal clock. When this standardization is used across a distributed network (applications running across mutliple distributed machines), it mitigates local system errors. A millisecond of difference 
each iteration can grow over long simulations and cause complications, thus the importance of instantiating a time-management system.

The following code block shows an example of real-time management in the Scalability example:

.. code-block:: python3

   def query_nist(host="pool.ntp.org", retry_delay_s=5, max_retry=5):
    for i in range(max_retry):
        try:
            logging.info(f"Contacting {host} to retrieve wallclock offset.")
            response = ntplib.NTPClient().request(host, version=3, timeout=2)
            offset = timedelta(seconds=response.offset)
            logging.info(f"Wallclock offset updated to {offset}.\nWaiting for manager start command.")
            return offset
        except ntplib.NTPException:
            logging.warning(
                f"Could not connect to {host}, attempt #{i+1}/{max_retry} in {retry_delay_s} s."
            )
            time.sleep(retry_delay_s)

The 'query_nist' function calls "pool.ntp.org", which will submit a request for the time to the NIST servers. When the time was returned, this 'real' time is compared to the local time, and the offset is accounted for. 
By constantly monitoring the offset of the internal local clock on each individual machine, the user can ensure that each application is running synchronisly across a scenario. This function aids in time mangement in a dispersed system where applications mimic
behaviors of a system in real time.
 
