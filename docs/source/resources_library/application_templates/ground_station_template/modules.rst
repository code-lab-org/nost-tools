.. _groundTemplate:

Ground Station
==============

The ground station template provides functionality for modeling uplinks and downlinks from spacecraft. You can find these files within the nost-tools/examples/ground_station folder after you :ref:`clone the GitHub repository <installation>`. For each included ground station, the application will publish a latitude/longitude location and a minimum elevation angle relative to the local horizon such that a satellite can begin transmitting stored mission data. The definition of elevation angle isn't completely consistent across fields, here it means the angle between the ground and a cone above the ground station where the satellite is visible. In the figure below, the green satellite is visible and the red one is not. The elevation angle is denoted by :math:`{\theta}`.Using these parameters you can determine if a satellite is in view for communications. 

.. image:: media/elevAngle.png
   :align: center
   :alt: Definition of Elevation Angle
   :width: 8 in

Please note that this template is built as a *managed* application - meaning that it responds to control events from the NOS-T :ref:`manager application <manager_template>`. An in-depth description of the Manager and these control events is :ref:`found here <icdManager>`. 


.. toctree::
  :maxdepth: 1

  main_ground
  config
  schemas