.. _groundTemplateConfig:

config.py
=========

This file contains the parameters required for modeling a basic ground station. They are simply the location of the ground station in latitude and longitude, and the elevation angle. The definition of elevation angle isn't completely consistent across fields, here it means the angle between the ground and a cone above the ground station where the satellite is visible. In the figure below, the green satellite is visible and the red one is not. The elevation angle is denoted by :math:`{\theta}`.

.. image:: media/elevAngle.png
   :align: center
   :alt: Simplified architecture diagram of the basic satellite template
   :width: 8 in

You have the ability to use this template to represent any number of ground stations. Note that in the code below, there are two :obj:`data` lists within the dataframe, the bottom one being commented-out. The commented-out section is an example of how you can implement multiple ground stations. 

.. literalinclude:: /../../examples/application_templates/ground_station_template/main_ground.py
  :lines: 4-
