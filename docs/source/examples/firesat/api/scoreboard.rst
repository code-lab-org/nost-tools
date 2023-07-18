Scoreboard
==========

*Unmanaged application written in JavaScript leveraging the CesiumJS platform to visualize FireSat+ test cases.*

Below is an example view of what the Scoreboard looks like. The yellow (detected) and red (ignited) dots represent fires.
The pink dots and cones represent ground stations and their elevation angles. The blue dots and cones is a spacecraft
and its field of regard.

.. image:: media/fireSatScoreboard.png
   :width: 600
   :align: center

Cesium Access Token and Assets
------------------------------

The Scoreboard uses the Cesium geospatial visualization tool which requires getting an access token.
You will get an access token by signing in at the following link:

https://cesium.com/ion/signin/tokens

After creating an account, you *must* add the Asset “Blue Marble Next Generation
July, 2004” from the Asset Depot (ID 3845) to the account assets to enable
visualization.

scoreboard.html
---------------

.. js:autofunction:: handleMessage
    :noindex:

The first 19 lines of this code is the .html "head," which is the framework on which the JavaScript below fills in. The JavaScript "body" begins on line 21.

An important section that will require editing is betwen lines 41-45. This part of the code pulls credentials from an env.js file. You will need to create a file named "env.js" and include the following information:

::

  var HOST="your event broker host URL"
  var PORT=#### - your connection port
  var USERNAME="your event broker username"
  var PASSWORD="your event broker password"
  var TOKEN="your Cesium token (see Cesium installation instructions)"



The `CesiumJS documentation <https://cesium.com/learn/cesiumjs/ref-doc/index.html>`_ contains descriptions of the different functions. Also, the `Cesium "Sandcastle" <https://sandcastle.cesium.com/>`_ sandbox environment is useful for rapid testing of these functions. Note that you will not be able to copy-and-paste the Scoreboard code directly into Sandcastle due to fundamental differences between it and the NOS-T event-driven architecture. However, the Sandcastle envrionment is useful for testing out the different visualization functions statically, and generating code snippets, before implementing them into a NOS-T application.