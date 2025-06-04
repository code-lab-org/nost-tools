.. _start-access-key:
The scoreboard application uses the Cesium geospatial visualization tool which requires getting an access token and an 3D Earth map asset. You will get an access token by signing in at the following link: https://cesium.com/ion/signin/tokens

After creating an account, you *must* add the Asset “Blue Marble Next Generation July, 2004” from the `Asset Depot (ID 3845) <https://ion.cesium.com/assetdepot/3845>`__ to your account assets to enable visualization.

.. _end-access-key:

.. _start-env-setup:
The Scoreboard application is in .html, and pulls in credentials from a JavaScript file. To do this create a text file with the name "env.js" containing the following information:

::

  var HOST="your event broker host URL"
  var PORT="your event broker port"
  var USERNAME="your event broker username"
  var PASSWORD="your event broker password"
  var TOKEN="your Cesium token (see Cesium installation instructions)"

For example, if you are running the test suite on your local computer using a local RabbitMQ event broker, you can set up the env.js file like this:

::

  var HOST="localhost"
  var PORT=15670
  var USERNAME="admin"
  var PASSWORD="admin"
  var TOKEN="your Cesium token (see Cesium installation instructions)"

.. note::

  For details on setting up a local RabbitMQ broker, refer to the :ref:`localBroker` guide.

.. _end-env-setup: