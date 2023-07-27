Visualizations
==============

This test suite contains two types of dynamic visualizations, both of which are unmanaged applications. Although these are used in conjunction with the managed applications of this test suite, they do not subscribe to :obj:`Manager` messages. These applications are strictly subscribers, they do not publish any messages to any topic endpoints on the message broker.

CesiumJS Scoreboard
-------------------

This is similar to the FireSat+ scoreboard.

|


SatelliteStorage State Dashboard
--------------------------------

.. automodule:: examples.downlink.scoreboard.downlinkDashboard
  :noindex:
  :show-inheritance:
  :member-order: bysource
  :exclude-members: examples.downlink.scoreboard.downlinkDashboard.on_message, examples.downlink.scoreboard.downlinkDashboard.update_capacity, examples.downlink.scoreboard.downlinkDashboard.update_cost, examples.downlink.scoreboard.downlinkDashboard.disable_dash

.. automethod:: examples.downlink.scoreboard.downlinkDashboard.on_message

.. automethod:: examples.downlink.scoreboard.downlinkDashboard.update_capacity

.. automethod:: examples.downlink.scoreboard.downlinkDashboard.update_cost

.. automethod:: examples.downlink.scoreboard.downlinkDashboard.disable_dash