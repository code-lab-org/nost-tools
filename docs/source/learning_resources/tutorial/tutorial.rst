.. _tutorial:

Hands-on Tutorial
=================

This tutorial contains information for those who are just starting out and builds up to show how complex test suites can be built.

Introduction
------------

The New Observing Strategies Testbed (NOS-T) is a computational environment to
develop, test, mature, and socialize new operating concepts and technology for
NOS. NOS-T provides infrastructure to integrate and orchestrate user-contributed
applications for system-of-systems test cases with true distributed
control over constituent systems. The overall concept, illustrated below, 
interconnects individual user applications and a NOS-T manager
application via common information system infrastructure to coordinate
the execution of virtual Earth science missions. NOS-T enables principal
investigators to conduct test runs in the same environment,
systematically changing variables to assess the overall efficacy of the
proposed new observing strategies. Recorded data and outcomes provide
evidence to advance technology readiness level and improve or innovate
upon existing Earth science measurement techniques.

Setup
-----

This section will show you how to set up NOS-T assuming you are a beginner to both coding and the testbed.

Integrated Development Environment (IDE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An IDE will make developing applications and interacting with the testbed much easier. The developers have mostly used `Spyder <https://www.spyder-ide.org/>`__
and Microsoft's `Visual Studio Code <https://visualstudio.microsoft.com/>`__. Going forward, this tutorial will assume that you are using one of these IDE's
or something similar.

NOS-T Tools Download and Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way to get the NOS-T tools library and example codes is to clone the NOS-T git repository
and install the tools. 

Cloning the Repository
^^^^^^^^^^^^^^^^^^^^^^

There are several ways to clone a git repository. `Here <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository?tool=webui>`__
is a good description of some of them.

Then, you need to clone the repository from the following link:

https://github.com/code-lab-org/nost-tools

Installing NOS-T tools requires pip version 23 or greater. Install via

::
  
  python -m pip install --upgrade pip

Then, from a command prompt,  navigate to the root directory 
(the location where you cloned the library) and install by running the following command:

:: 
  
  pip install -e .[examples]


Following the instructions above will automatically install the python packages that NOS-T depends on to run. These package dependencies can
otherwise be found in the `requirements file <https://github.com/code-lab-org/nost-tools/blob/main/pyproject.toml>`__.

.. _tutorialSystemDescription:

NOS-T System description
------------------------

The NOS-T system architecture follows a loosely coupled event-driven
architecture (EDA) where member applications communicate state changes
through events that are embodied as notification messages sent over a
network. These event/message payloads contain the relevant data for communicating these state changes. EDA provides enhanced scalability and reliability over other software architectures by replicating event handling functions across
infrastructure instances while maintaining modularity between
applications through a simple event-handling interface. NOS-T can also
be described as a service-oriented architecture (SOA) as applications
trigger services in response to events.

The NOS-T architecture relies on a centralized infrastructure component
called an event broker (synonymous with message broker) to exchange
event notifications between applications. A broker simplifies the
communication structure because each member application (client) only
directly connects to the broker, rather than requiring each application
to directly connect to every other application.

The FireSat+ Test Suite
-----------------------

From here, the tutorial will explain important functions using FireSat+, an example NOS-T test suite based on FireSat, the common space systems 
engineering application case. The operational concept for FireSat+ is that one or several satellites are searching for fires. The fires are ignited following a historical dataset. When one of the satellites orbit above these locations, it will detect the fire. Finally, once that satellite is in range of a ground station, it will report the fire.

This is a graphical representation of the FireSat+ message flows and their payloads. 

.. image:: media/fireSatWorkflow.png
   :width: 400
   :align: center

|

For more information on FireSat+, please see the following:

* The Interface Control Document has a high-level description of FireSat+ :ref:`here <ICDfireSat>`.
* A deeper dive into the applications and code is :ref:`here <fireSatExampleTop>`.
* A paper describing this test suite is `here <https://doi.org/10.1109/IGARSS46834.2022.9883290>`__.

NOS-T test suites are made up of applications communicating over the broker. Next, the tutorial will detail two of the FireSat+ apps to give you a better idea of how they work. 

.. _tutorialSat:

The **Satellites** application - main_constellation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A key component of the FireSat+ example case is **Satellite** application. This application enables the user to generation a satellite constellation using the nost-tools library, leveraging predefined templates to construct a model of a real-life constellation. You will be guided through the how each code block works, to help understand the purpose of different components in an application.

First, you'll need to create a new file titled main_constellation.py inside your examples/firesat_tutorial/satellites folder. To progress through this section, copy and paste the code blocks into this file. NOTE: You *must* maintain the indentations you see in these code blocks when pasting them into the main_constellation.py file.

This first part of the code contains import statements allow you to install the necessary dependencies to construct the application. The group at the top are regular Python dependencies while the ones at the bottom draw from the :ref:`NOS-T tools library <nostTools>`.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 8-20

This next set of import statements are customized for FireSat+ values from the constellation configuration files. The first set of imports draws in the message schema configuration, which defines the structure of how **Satellites** communicates data. The second set of imports pulls in values to define the constellation: the ``PREFIX`` the messages will be published on, the ``NAME`` of the satellite, the ``SCALE`` of the timed simulation, 
the two-line element sets (``TLEs``) that define the satellites' orbit, and the ``FIELD_OF_REGARD``, which indicates the region visible on Earth by the satellite's instrument.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 22-35

The first line in the code block below sets up a logger to help you track what is going on. More info on the various levels can be found
`here <https://docs.python.org/3/howto/logging.html#when-to-use-logging>`__. Next, the function, ``compute_min_elevation``, returns the minimum elevation angle required for a satellite to observe a point from it's current location. It accepts the parameters altitude and field_of_regard to 
complete mathematical functions to return the degree on minimum elevation.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 37-63
 
Next, the ``compute_sensor_radius`` function  pulls in the result of compute_min_elevation and the altitude value to return ``sensor_radius``, which provides the radius of the nadir pointing sensor's circular view projected onto Earth. 

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 66-89

The ``get_elevation_angle`` is a function that uses the Skyfield library. It accepts the parameters ``t``, ``sat``, and ``loc``. The first two, respectively, represent the Skyfield time object, the Skyfield EarthSat object. The third is the latitude/longitude of the spacecraft's subpoint, along with the spacecraft altitude. It returns an elevation angle in respect to the topocentric horizon.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 92-109

These two functions, ``check_in_view`` and ``check_in_range``, affirm if the elevation angle and immediate location of the satellite enable it to connect to a ground station and view regions on Earth. 

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 112-159

.. _tutorialConstellation:

Constellation class
~~~~~~~~~~~~~~~~~~~

The next section of code blocks define the Constellation class. In object-oriented programming, a class is a replicable object that can be assigned unique parameters to generate a diverse collection of similar objects.
The Constellation class leverages the NOS-T tools library 'Entity' object class to construct the constellation chain.

The first two functions in the Constellation class, ``init`` and ``initialize``, prepare the test run for startup by initializing data.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 162-239

The next two functions, ``tick`` and ``tock``, are very important for executing time-managed test suites. Generally, the ``tick`` function computes the current state of an application. Any cumbersome functions like simulations should be performed here. The ``tock`` function commits the state changes. You want this done as quickly as possible to maintain consistent timing between applications.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
  :lines: 241-317

The next function, ``on_fire``, checks the current simulation time vs. a database of actual fires detected by an space-based infrared sensor. This function then publishes a message containing information about the fire. It also maintains an internal database for when fires are detected and reported, and which satellite did the detecting/reporting.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
  :lines: 319-354

The final block of the Constellation class is next. It contains the ``on_ground`` function which is used to collect information on ground station locations and elevation angles when those messages are published.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
  :lines: 356-392

Position Publisher Class
~~~~~~~~~~~~~~~~~~~~~~~~

The next class in the **Satellites** application is the Position Publisher. This class takes the satellite location information from the Constellation class and publishes it over the NOS-T infrastructre. These messages are used for the **Scoreboard** application, which is a geospatial visualization tool.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 395-460

Fire Observer Classes
~~~~~~~~~~~~~~~~~~~~~

The next code block contains two different fire observation classes. The first of these is for detecting fires and the second is for reporting fires. The concept of operations for FireSat+ is that fires are first *ignited*, then *detected* when a satellite passes over them. Finally, the fires are *reported* when the detecting satellite is in range of a ground station for the data downlink. The Fire Observer classes publish this over the testbed for postprocessing of results, and for **Scoreboard** visualization.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 463-523

The final block of code in the **Satellites** app is for initializing data and adding the functions and classes.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 526- 574


The **Manager** application - main_manager.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Maintaining a consistent simulation clock is important for many NOS-T use cases. For test suites that need to run faster than real time,
it is an absolute necessity. The NOS-T **Manager** application is a good way to orchestrate all of the pieces for these types of tests.
The manager is included in the NOS-T Tools library and will ensure that compliant applications start at the same time, and use a consistent
simulation clock throughout the test run. 

As above with the **Satellites** application, you should create a blank main_manager.py file in the examples/firesat_tutorial/manager folder. 
NOTE: You *must* maintain the indentations you see in these code blocks when pasting them into the main_manager.py file.

Next, we will go through the Manager code block-by-block to understand what it is doing. First, we have all of the import statements that the 
**Manager** relies on. The first of these three are general Python dependencies, and the
second two are drawn from the NOS-T tools library. The last imports come from a config file that you should adjust for any specific test suites.
In that config file you will need to set your desired event message prefix, the time scale, and any time scale updates. 

.. literalinclude:: /../../examples/firesat/manager/main_manager.py
	:lines: 12-26

.. _timeScaleUpdate:

The time scale is a simple multiplier, i.e. if :code:`SCALE = 60` then the time will be sped up by 60x -- meaning that each second of real time
will be one minute of simulation time. The time scale updates are used when you want to change the time scale at any point during 
the simulation. As for the updates, They take a form like this:

:code:`UPDATE = [TimeScaleUpdate(120.0, datetime(2020, 1, 1, 8, 20, 0, tzinfo=timezone.utc))]` 

The above command would change the time scale to 120x at the given datetime object in simulation time. If you do not wish to update the time scale
during a test case, then you can set 

:code:`UPDATE = []`

Finally, the last line in the above code block sets up a logger to help you track what is going on. More info on the various levels can be found
`here <https://docs.python.org/3/howto/logging.html#when-to-use-logging>`__.

The next block of code starts with a name guard and credentials like the **Satellites** app above. These credentials will be drawn from an environment 
file :ref:`described below<envSetUp>`. The next four lines of code follow their preceding comments. Using the various NOS-T tools from the library the connection is set, the manager application is created, it is set to shut down after the test case, and is commanded to start up.

.. literalinclude:: /../../examples/firesat/manager/main_manager.py
	:lines: 29-45

This final section of code contains the vital information for executing your test plan. The comments on the right side give a good explanation of 
what each line means. It is important to note that the :code:`SCALE` and :code:`UPDATE` values should be set in the config file as explained 
:ref:`above <timeScaleUpdate>`.

.. literalinclude:: /../../examples/firesat/manager/main_manager.py
	:lines: 48-58

Test Suite Wrap-Up
------------------

Next, we'll go through the next steps to actually executing FireSat+.

File Tree Checkup
~~~~~~~~~~~~~~~~~

If you have done everything correctly up to this point, you should see a file tree like the image below. Most importantly, you should have 
the five folders in the firesat folder which contain the constituent FireSat+ applications. These applications are described in the next section.

.. image:: media/fileTree.png
   :width: 400
   :align: center

Remaining Applications
~~~~~~~~~~~~~~~~~~~~~~

There are a total of five files you will need to run for FireSat+, four user applications, the NOS-T manager application,
and the **Scoreboard**, a geospatial data visualization tool. 
Managing an NOS-T Test Run


Executing the FireSat+ Test Suite
---------------------------------

There are a few more steps necessary to run FireSat+. You need to create a Cesium token to run the **Scoreboard** and set up
environment files for each application.

Cesium Access Token and Assets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The FireSat+ Scoreboard application uses the Cesium geospatial visualization tool which requires getting an access token
and an 3D Earth map asset. You will get an access token by signing in at the following link:

https://cesium.com/ion/signin/tokens

After creating an account, you *must* add the Asset “Blue Marble Next Generation
July, 2004” from the `Asset Depot (ID 3845) <https://ion.cesium.com/assetdepot/3845>`__ to your account assets to enable
visualization.

.. _envSetUp:

Setting Up Environment Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to protect your (and our) information, these applications all use
environment files for usernames, passwords, event broker host site URLs, and
port numbers. You will need to create an environment file in the each FireSat+ folders.

Note that you can use most text editors to make these files but be sure that you are not saving them as a .txt file type.
For instance, if you save a .evn file as a .txt file type using Windows Notepad, it will actually save as .evn.txt which will
not work. If you're using Windows Notepad choose the file type "All Files (*.*)".

For the applications coded in python (.py files) you will need to create a text
file with the name ".env" containing the following text:

::

  HOST="your event broker host URL"
  PORT=8883 - your connection port
  USERNAME="your event broker username"
  PASSWORD="your event broker password"

The Scoreboard application is in .html, and pulls in credentials from a JavaScript file. To do this create a text file with the name "env.js" containing the following information:

::

  var HOST="your event broker host URL"
  var PORT=8883 - your connection port
  var USERNAME="your event broker username"
  var PASSWORD="your event broker password"
  var TOKEN="your Cesium token (see Cesium installation instructions)"



Executing FireSat+
~~~~~~~~~~~~~~~~~~

Finally, you need to run the five applications together in order to execute the FireSat+ test suite. These applications need to be
logically separated when running. For the python scripts, this can be done by running them on separate computers, 
by using separate consoles in Spyder, or separate terminals with VSCode. The **Scoreboard** is an .html file
and can be run in a web browser, double-clicking the file should work.  Each folder in the FireSat+ test suite
has a code you need to run, they are:

* main_fire.py - The **Fires** app publishes historical fire data.
* main_ground.py - The **Ground** app models a ground station in Svalbard, Norway.
* main_constellation.py - The **Satellites** app models the constellation of spacecraft observing and reporting the fires.
* scoreboard.html - The aforementioned **Scoreboard** gives a view of what's happening during a test run.
* main_manager.py - The NOS-T **Manager** app orchestrates each test run by starting the other apps at the same time, maintaining a consistent time throughout, and shutting down the apps at the end.

You **must** run the main_manager.py application last, otherwise it does not matter in which 
order you start the other applications. All of the .py applications will give an output that
they are waiting for the test case to start up. 

If everything is running correctly, the Scoreboard app should show an image similar
to below.

.. image:: media/fireSatScoreboard.png
   :width: 600
   :align: center

Conclusion
----------

This hands-on tutorial was developed to help users get started with NOS-T from a basic level. It begins with
downloading an IDE for running scripts to interface with NOS-T and finishes with executing the FireSat+ example code. Some good next
steps for learning other NOS-T functions and developing your own test suites can be found at the following links:

* :ref:`Main FireSat+ documentation <fireSatExampleTop>`
* :ref:`Science Event Dashboard test suite walkthrough <instructionsScienceDash>`
* :ref:`NOS-T Tools API documentation <nostTools>`

