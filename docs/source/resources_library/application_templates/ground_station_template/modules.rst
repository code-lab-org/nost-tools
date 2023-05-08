.. _groundTemplate:

Ground Station
==============

The ground station template provides functionality for modeling uplinks and downlinks from spacecraft. In its basic form here, the ground station application will publish a lat/lon location and elevation angle. Using these paramters you can determine if a satellite is in view for communications. You can find these files within the nost-tools/examples/ground_station folder after you :ref:`clone the GitHub repository <installation>`. 



Please note that this template is built as a *managed* application - meaning that it responds to control events (red box with sharp edges in the above figure) from the included NOS-T application. These include initialization, startup, and timing commands - an in-depth description is :ref:`found here <icdManager>` It does not matter if main_manager.py is in the same folder as the other files or not.


.. toctree::
  :maxdepth: 1

  config