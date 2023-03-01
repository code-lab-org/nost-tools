.. _instructionsFireSat:

FireSat+
========

This guide contains step-by-step instructions for running the FireSat+ test
suite. This is based on the FireSat mission seen in *Space Mission
Analysis and Design, Third Edition* by James R. Wertz and Wiley J. Larson
(1999). In contrast to the Science Dashboard example test suite, the FireSat+ 
test suite uses the NOS-T tools library and provides an example for how 
to create a more capable application case than the Science Event Dashboard.

* The Interface Control Document has a high-level description of FireSat+ here: :ref:`ICDfireSat`.
* A deeper dive into the applications and code is here: :ref:`fireSatExampleTop`.

The Interface Control Document contains a more in-depth description of 
FireSat+ here :ref:`ICDfireSat`

FireSat+ Applications and NOS-T Tools Installation
--------------------------------------------------

In order to run a FireSat+ test case you need to clone the NOS-T git repository
and install the NOS-T tools library. There are several ways to clone a git repository. `Here <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository?tool=webui>`__
is a good description of some of them.
 
First, you need to clone the repository from the following link:

https://github.com/code-lab-org/nost-tools

Then, from a command prompt,  navigate to the root directory 
(the location where you cloned the library) and install by running the following command:

:: 
  
  pip install -e .



Cesium Access Token and Assets
------------------------------

The FireSat+ Scoreboard application is a great way to visualize what is happening during a test.
It uses the Cesium geospatial visualization tool which requires getting an access token.
You will get an access token by signing in at the following link:

https://cesium.com/ion/signin/tokens

After creating an account, you *must* add the Asset “Blue Marble Next Generation
July, 2004” from the Asset Depot (ID 3845) to the account assets to enable
visualization.

Setting Up Environment Files
----------------------------

In order to protect your (and our) information, these applications all use
environment files for usernames, passwords, event broker host site URLs, and
port numbers.

For the applications coded in python (.py files) you will need to create a text
file with the name ".env" containing the following text:

::

  HOST="your event broker host URL"
  PORT=#### - your connection port
  USERNAME="your event broker username"
  PASSWORD="your event broker password"

The Scoreboard application is .html, and therefore the environment needs
to be set in a JavaScript file. To do this create a text file with the name
"env.js" containing the following information:

::

  var HOST="your event broker host URL"
  var PORT=#### - your connection port
  var USERNAME="your event broker username"
  var PASSWORD="your event broker password"
  var TOKEN="your Cesium token (see Cesium installation instructions)"

Running FireSat+
----------------

In order to run FireSat+, you will need to start each application separately. The
Key main files for each application are named main_XYZ.py for the Python applications
and scoreboard.html for the data visualization tool. These applications need to be
logically separated. This can be done by running them on separate computers, or 
by using separate consoles in Spyder, or terminals with VSCode.

You should start the main_manager.py application last, otherwise it does not matter in which 
order you start the other applications. All of the .py applications will give an output that
they are waiting for the test case to start up. The scoreboard.html application should
be opened in a web browser.

If everything is running correctly, the Scoreboard app should show an image similar
to below.

.. image:: media/fireSatScoreboard.png
   :width: 600
   :align: center

| 
| Next is a graphical representation of the FireSat+ message flows and their payloads. 

.. image:: media/fireSatWorkflow.png
   :width: 600
   :align: center

