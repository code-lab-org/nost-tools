.. _examples:

Example Test Suites
===================

These four example test suites demonstrate both managed and unmanaged application use cases.
Descriptions of each participating application and standardized message schema can be found via the links below. 

The :ref:`Science Event Dashboard<instructionsScienceDash>` is a simple example with only two applications to demonstrate publish-subscribe relationships and dashboards for results visualization.

:ref:`FireSat+<fireSatExampleTop>` is a more complex and capable use case which makes use of the NOS-T tools library for most applications. There
is a step-by-step guide for running this test suite in the :ref:`tutorial`.

The :ref:`Downlink Test Suite<downlink>` is derivative of the `FireSat+` suite, but with additional capabilities and standardized message schema. The grounds application in particular is much more active than in the `FireSat+` test suite, as downlink times and associated costs are tracked for every downlink opportunity to a ground station, and the availability of a ground station can change state dynamically during the simulation. While there is no equivalent of the fires application, this test suite does expand on the dashboard capabilities introduced in the `Science Event Dashboard` example.

Finally, the :ref:`Scalability Test Suite<scalability>` was used to test how well NOS-T can handle messages loads of varying frequency and size.

.. toctree::
   :maxdepth: 1

   scienceDash/api/modules
   firesat/api/modules
   downlink/api/modules
   scalability/api/modules
   
