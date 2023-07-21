.. _nostTools:

NOS-T Tools API
---------------

This page contains descriptions of the NOS-T tools library features, and provides a detailed description of their functions. Within this library, there are templates to support both time-managed and time-agnostic applications. These templates contain commonly-used functions for distributed space missions. The first step for using the tools library is to follow the :ref:`installation instructions <installation>`. 

The tools have been split up into the three following sections:

* **Message Schemas**:  These define the information carried in common message payloads and the format that information should take. They use the Pydantic data validation library. They are split between command and status messages.

  * *Command messages*:  Used by the manager to control time-managed scenarios. These are further described in :ref:`this section <controlEvents>` of the Interface Control Document (ICD).

  * *Status messages*:  Used by all constituent applications to update simulation time and modes. There is also :ref:`a section <statusEvents>` in the ICD for these.

* **Simulator Objects**:  This collection of Python objects help manage state changes for simulation applications. They include functions that can compute (tick) and commit (tock) these state changes as well as those that control enumerate simulation modes and handle scenario timing.

* **Applications Objects**:  These Python objects help the constituent applications communicate with the MQTT messaging protocol. They include functions that connect to a MQTT broker, publish messages and defined intervals, and help to develop applications that can interface with the NOS-T manager.

Clicking into the three sections listed above will bring you to the automatically-generated documentation. You can see which of the NOS-T tools Python scripts contains the given schema or object by looking at the top-level titles. For example, the ConnectionConfig function has the following title:  :code:`nost_tools.application_utils.ConnectionConfig`. This means that function is found, and can be imported from, the *application_utils.py* file.

The :ref:`NOS-T Example Test Suites <examples>` are a good place to see how the tools library can be implemented. In particular, all of the Python :ref:`FireSat+ <fireSatExampleTop>` applications use the tools. Furthermore, the :ref:`example application templates <appTemplates>` are a collection of bare-bones templates, similar to FireSat+, with some of the tools functionality built-in.

.. toctree::
  :maxdepth: 1


  schemas
  simulator
  application