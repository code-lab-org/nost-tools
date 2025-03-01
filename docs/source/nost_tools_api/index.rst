.. _nostTools:

API Reference
-------------

This page contains descriptions of the NOS-T tools library features, and provides a detailed description of their functions. Within this library, there are templates to support both time-managed and time-agnostic applications. The first step for using the tools library is to follow the :ref:`installation instructions <installation>`. 

The tools consist of ten Python files defining useful methods and classes. For logical convenience they are categorized into the following three sections:

* **Message Schemas**:  
		Define the information carried in common message payloads and the format that information should take using the Pydantic data validation library.
			
			*	*Command messages*:  Used by the manager to control time-managed scenarios. These are further described in :ref:`this section <controlEvents>` of the Interface Control Document (ICD).
			
			*	*Status messages*:  Used by all constituent applications to update simulation time and modes. These are further described in :ref:`this section <statusEvents>` of the ICD.

* **Simulator Objects**:  
		Manage state changes and internal clocks for simulation applications.

			*  *Observer Objects*:  Implement patterns for loosely coupling observables and observers.
			
			*  *Scenario Objects*:  Define states and methods for executing a simulation.

* **Applications Objects**:  
		Help constituent applications connect to the MQTT message broker and communicate with the MQTT messaging protocol.
		
			*  *Utilities*:  Monitor and report on application connections, modes, and time statuses.
			
			*  *Publishers*:  Define patterns for publishing messages on regularly spaced time-intervals.
			
			*  *Applications*:  Serve as templates or wrappers of basic MQTT client functionality and synchronization for simulation.
			

.. toctree::
  :maxdepth: 1


  schemas
  simulator
  application

The :ref:`NOS-T Example Test Suites <examples>` feature many different implementations of the tools. In particular, all of the Python :ref:`FireSat+ <fireSatExampleTop>` applications make use of the NOS-T tools library for a faster than real-time simulation that requires coordination from a **Manager** application. Furthermore, the :ref:`example application templates <appTemplates>` include a collection of bare-bones templates, similar to *FireSat+*, with some of the tools functionality built-in.