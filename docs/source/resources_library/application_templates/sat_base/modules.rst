.. _basic_satellite:

Basic Satellite
===============

This set of Python scripts model a basic satellite. It's main functions are to propagate an orbit from Two-Line Elements, check if a point on Earth is within a set field of regard, and see if a ground station is viewable. You can find these files within the nost-tools/examples/satBaseClass folder after you :ref:`clone the GitHub repository <installation>`. 

Please note that this template is built as a *managed* application - meaning that it responds will need to use the NOS-T **Manager** applicaion. While a **Manager** template is coming soon, an example can be found in the :ref:`FireSat+ example test suite <fireSatMgr>`.

.. toctree::
  :maxdepth: 1

  main_sat
  satellite
  schemas
  config