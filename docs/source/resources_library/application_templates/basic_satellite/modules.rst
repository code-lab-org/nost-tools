.. _basic_satellite:

Basic Satellite
===============

This set of Python scripts model a basic satellite. It's main functions are to propagate an orbit from Two-Line Elements, check if a point on Earth is within a set field of regard, and see if a ground station is viewable. You can find these files within the nost-tools/examples/satBaseClass folder after you :ref:`clone the GitHub repository <installation>`. 

Please note that this template is built as a *managed* application - meaning that it responds to initialization and startup commands from the included NOS-T :ref:`Manager <satBaseManager>` application. 

.. toctree::
  :maxdepth: 1

  main_sat
  satellite
  schemas
  config
  main_manager