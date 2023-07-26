Scoreboard
==========

*Unmanaged application written in JavaScript leveraging the CesiumJS platform to visualize FireSat+ test cases.*

The **Scoreboard** application gives a geospatial view of the mission. This and other mission visualization appliations have been essential for ensuring that test cases are behaving as intended. Running the **Scoreboard** requires a CesiumJS account, access token, and the Blue Marble asset.

Cesium Access Token and Assets
------------------------------

The Scoreboard uses the Cesium geospatial visualization tool which requires getting an access token.
You will get an access token by signing in at the following link:

https://cesium.com/ion/signin/tokens

After creating an account, you *must* add the Asset “Blue Marble Next Generation July, 2004” from the Asset Depot (ID 3845) to the account assets to enable visualization.

env.js file
-----------

The Scoreboard application pulls credentials from a JavaScript file. To set this up create a text file with the name "env.js" containing the following information:

::

  var HOST="your event broker host URL"
  var PORT=8883 - your connection port
  var USERNAME="your event broker username"
  var PASSWORD="your event broker password"
  var TOKEN="your Cesium token (see Cesium installation instructions)"

scoreboard.html
---------------

This is the main file for the **Scoreboard** application and can be run in a regular web browser. There isn't a separate config file like the other FireSat+ applications. The detailed description for scoreboard.html is commented in the code.

Cesium resources
----------------

The `CesiumJS documentation <https://cesium.com/learn/cesiumjs/ref-doc/index.html>`_ contains descriptions of the different functions. Also, the `Cesium "Sandcastle" <https://sandcastle.cesium.com/>`_ sandbox environment is useful for rapid testing of these functions. Note that you will not be able to copy-and-paste the Scoreboard code directly into Sandcastle due to fundamental differences between it and the NOS-T event-driven architecture. However, the Sandcastle envrionment is useful for testing out the different visualization functions statically, and generating code snippets, before implementing them into a NOS-T application.

Finally, below is an example view of what the Scoreboard looks like. The yellow (detected) and red (ignited) dots represent fires.
The pink dots and cones represent ground stations and their elevation angles. The blue dots and cones is a spacecraft
and its field of regard.

.. image:: media/fireSatScoreboard.png
   :width: 600
   :align: center
