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

This section will show you how to set up NOS-T starting from zero.

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

Then, from a command prompt,  navigate to the root directory 
(the location where you cloned the library) and install by running the following command:

:: 
  
  pip install -e .


Following the instructions above will automatically install the python packages that NOS-T depends on to run. These can
otherwise be found in the `requirements file <https://github.com/code-lab-org/nost-tools/blob/main/docs/requirements.txt>`__

NOS-T System description
------------------------

The NOS-T system architecture follows a loosely coupled event-driven
architecture (EDA) where member applications communicate state changes
through events that are embodied as notification messages sent over a
network. EDA provides enhanced scalability and reliability over other
software architectures by replicating event handling functions across
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

Application Build 1
-------------------

From here, the tutorial will explain important functions using FireSat+, an example NOS-T test suite based on FireSat, the common space systems 
engineering application case. The **Satellites** application


Application Build 2
-------------------

Maintaining a consistent simulation clock is important for many NOS-T use cases. For test suites that need to run faster than real time,
it is an absolute necessity. The NOS-T **Manager** application is a good way to orchestrate all of the pieces for these types of tests.

Test Suite Wrap-Up
------------------

asdf

File Tree Checkup
~~~~~~~~~~~~~~~~~

asdf

Remaining Applications
~~~~~~~~~~~~~~~~~~~~~~

There are a total of five files you will need to run for FireSat+, four user applications, the NOS-T manager application,
and the **Scoreboard**, a geospatial data visualization tool. These applications need to be
logically separated when running. For the python scripts, this can be done by running them on separate computers, 
by using separate consoles in Spyder, or separate terminals with VSCode. The **Scoreboard** is an .html file
and can be run in a web browser, double-clicking the file should work.  Each folder in the FireSat+ test suite
has a code you need to run, they are:

* main_fire.py - The **Fires** app publishes historical fire data.
* main_ground.py - The **Ground** app models a ground station in Svalbard, Norway.
* main_constellation.py - The **Satellites** app models the constellation of spacecraft observing and reporting the fires.
* scoreboard.html - The aforementioned **Scoreboard** gives a view of what's happening during a test run.
* main_manager.py - The NOS-T **Manager** app orchestrates each test run by starting the other apps at the same time, maintaining a consistent time throughout, and shutting down the apps at the end.

Managing an NOS-T Test Run
--------------------------

asdf

Executing the FireSat+ Test Suite
---------------------------------

asdf

Environment Files
~~~~~~~~~~~~~~~~~

asdf

Conclusion
----------

This tutorial explained how to ...