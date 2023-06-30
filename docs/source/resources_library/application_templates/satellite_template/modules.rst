.. _basic_satellite:

Satellite Template
==================

This set of four Python scripts model a basic satellite. Its main functions are to propagate an orbit from Two-Line Elements, check if a point on Earth is within a set field of regard, and see if a ground station is viewable. You can find these files within the *examples/application_templates/satellite_template* folder after you :ref:`clone the GitHub repository <installation>`. 

Maintaining the current file structure, with  :ref:`satBaseMain` and :ref:`satBaseSatellite` in the top-level folder, and :ref:`satBaseSchemas` and :ref:`satBaseConfig` in the satellite_config_files folder will allow it to run without any changes. This architecture (seen in a diagram below) is *not* the only way to model a satellite in NOS-T, but has worked well for the development team. The black boxes with sharp edges denote the data being pulled in by the main_sat.py entry point code. 

.. image:: media/basicSatArch.png
   :align: center
   :alt: Simplified architecture diagram of the basic satellite template
   :width: 8 in
  
Simplified Architecture Diagram of the Basic Satellite Template

Please note that this template is built as a *managed* application - meaning that it responds to control events (red box with sharp edges in the above figure) from the included NOS-T :ref:`Manager <manager_template>` application. These include events which initialize, start up, and maintain consistent timing throughout the test case. An in-depth description of the Manager commands is :ref:`found here <icdManager>`. 

.. toctree::
  :maxdepth: 2

  main_sat
  satellite
  schemas
  config