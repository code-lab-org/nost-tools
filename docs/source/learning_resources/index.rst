.. _learningResources:

Learning Resources
==================

This section contains resources for helping users with NOS-T applications and test suites.

* The :ref:`Science Event Dashboard Test Suite <instructionsScienceDash>` will show you how to run two applications in an unmanaged test suite that doesn't use the NOS-T Tools library.
* The :ref:`FireSat+ Test Suite <tutorial>` guides you through the entire process of running managed applications using the NOS-T Tools library, from installing the NOS-T Tools library to executing the various applications, including ``Manager``, ``Satellite``, ``Ground``, and ``Fire``. These applications send messages using a RabbitMQ event broker.
* The :ref:`Downlink Test Suite <downlink>` is a derivative of the FireSat+ test suite, including ``Manager``, ``satelliteStorage``, ``Grounds``, and ``Outages``. These applications send messages using a RabbitMQ event broker.

Finally, the :ref:`Resource Library <resourceLibrary>` contains useful material such as application templates.

.. toctree::
   :maxdepth: 2
   :hidden: 

   science_dash/science_dash
   tutorial/tutorial
   downlink/downlink