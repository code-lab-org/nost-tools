NOS-T Science Event Test Suite
==============================

These two applications provide a basic demonstration on how to publish and
subscribe to topics with NOS-T. This example does not require the usage of the
NOS-T tools library.

One of the applications, scienceEventPublisher.py produces a "science event"
which has a random location and consistent utility curve associated with it.
It publishes these events in a message payload to a topic over the event broker.

The second application, scienceEventDashboard, subcribes to this topic and
then creates a visual dashboard to see the current "science utility" at each
simulation time step. These dashboards have been helpful for the development
team in ensuring that test behavior is as expected.

.. toctree::
  :maxdepth: 1

  scienceEventPublisher
  scienceEventDashboard
