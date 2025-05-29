.. _examples:

Example Test Suites
===================

The example test suites demonstrate both managed and unmanaged application use cases.
Descriptions of each participating application and standardized message schema can be found via the links below. 

.. rubric:: Unmanaged Applications

- :ref:`Science Event Dashboard<instructionsScienceDash>`: Simple example with only two applications to demonstrate publish-subscribe relationships and dashboards for results visualization.

- :ref:`Scalability<scalability>`: Used to test how well NOS-T can handle messages loads of varying frequency and size.

.. rubric:: Managed Applications

- :ref:`FireSat+<fireSatExampleTop>`: Complex and capable use case which makes use of the NOS-T tools library for most applications. There is a step-by-step guide for running this test suite in the :ref:`tutorial`.

- :ref:`Downlink Test Suite<downlink>`: A derivative of the `FireSat+` suite, but with additional capabilities and standardized message schema. The grounds application in particular is much more active than in the `FireSat+` test suite, as downlink times and associated costs are tracked for every downlink opportunity to a ground station, and the availability of a ground station can change state dynamically during the simulation. While there is no equivalent of the fires application, this test suite does expand on the dashboard capabilities introduced in the `Science Event Dashboard` example.

.. toctree::
   :maxdepth: 1
   :hidden:

   scienceDash/api/modules
   scalability/api/modules
   firesat/api/modules
   downlink/api/modules