.. _instructionsScienceDash:

Science Event Dashboard Test Suite
==================================

This example illustrates how to build a basic visualization tool using a publish-subscribe (pub/sub) architecture powered by a RabbitMQ event broker. It aims to help users understand how to visualize data flows within a test suite, with a focus on science event data.

.. note::
   This example does not require the full NOS-T tools library, making it accessible for users who want to implement similar functionality without the overhead of the entire tools suite.

Introduction
------------

NOS-T
~~~~~

.. include:: /../../docs/source/learning_resources/nost_description.rst

Science Event Dashboard Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Science Event Dashboard Test Suite is a simple example that not require the use of the NOS-T tools library. It contains two applications:

- **Science Event Publisher**: Publishes science event data, including utility scores and random locations.
- **Science Event Dashboard**: Visualizes the data published by the science event publisher using the Python Dash library.

The Science Event Publisher regularly publishes a utility score and globally distributed random location. The utility scores follow a parabolic curve from the apex down to zero for each time step.

The Science Event Dashboard is a basic dashboard which visualizes the utility and location information using the Python Dash library. The development team has found visualization tools like this dashboard to be very helpful to ensure that test behavior is as expected. 

A basic graphical representation of the data flow is shown below.

.. image:: media/scienceDashWorkflow.png
   :width: 600
   :align: center

|

Setup
-----

This section will show you how to set up NOS-T assuming you are a beginner to both coding and the testbed. The setup phase involves:

1. Integrated Development Environment Installation
2. NOS-T Tools Installation
3. RabbitMQ Event Broker Setup
4. Repository Cloning

Integrated Development Environment Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /../../docs/source/installation/installation.rst
  :start-after: start-ide-installation
  :end-before: end-ide-installation

NOS-T Tools Installation
~~~~~~~~~~~~~~~~~~~~~~~~

Although the Science Event Test Suite code does not require the full NOS-T Tools library, it is recommended to install the library to simplify installation of dependencies for this test suite.

.. include:: /../../docs/source/installation/installation.rst
  :start-after: start-nos-t-installation
  :end-before: end-nos-t-installation

RabbitMQ Event Broker Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Refer to the :ref:`localBroker` guide for instructions on how to set up a RabbitMQ event broker locally.

.. important::
  The test suite uses a RabbitMQ event broker to facilitate communication between applications. Ensure that your RabbitMQ broker is running and accessible before proceeding with the test suite.
|

Repository Cloning
~~~~~~~~~~~~~~~~~~

.. include:: /../../docs/source/installation/installation.rst
  :start-after: start-repository-cloning
  :end-before: end-repository-cloning

This will create a directory called ``nost-tools`` in your current working directory. Inside this directory, you will find the example code under the ``examples/scienceDash/`` folder.

.. note::
   
   More in-depth descriptions of what the code is doing can be found here: :ref:`scienceDashEX`.

Component Applications Overview
-------------------------------

The **Science Event Publisher** and **Science Event Dashboard** applications are the two main components of this test suite.

**Science Event Publisher**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **Science Event Publisher** is responsible for generating and publishing science event data, including utility scores and random locations. It uses the RabbitMQ event broker to send messages to the dashboard application.

The first section of the code includes import statements that bring in the necessary dependencies for building the publisher application. 

.. literalinclude:: /../../examples/scienceDash/scienceEventPublisher.py
	:lines: 8-14

Following the imports, the code establishes a connection to the RabbitMQ event broker using the provided environment variables in a ``.env`` file. It uses the `pika` library to create a connection and a channel for publishing messages.

.. literalinclude:: /../../examples/scienceDash/scienceEventPublisher.py
	:lines: 16-29

After establishing the connection, the code defines and declares a RabbitMQ exchange named `science_event`. This exchange is used to route messages to the appropriate queues based on the routing key.

.. literalinclude:: /../../examples/scienceDash/scienceEventPublisher.py
	:lines: 31-33

Finally, the code defines a function to generate random locations and utility scores. The utility scores are generated using a parabolic curve, which is calculated based on the current time step.

.. literalinclude:: /../../examples/scienceDash/scienceEventPublisher.py
   :lines: 35-

**Science Event Dashboard**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **Science Event Dashboard** is a visualization tool that subscribes to the messages published by the Science Event Publisher. It uses the Python Dash library to create a web-based dashboard that displays the utility scores and locations in real-time.


The first section of the code includes import statements that bring in the necessary dependencies for building the dashboard application.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
	:lines: 9-18

The function ``on_message`` handles incoming messages from the RabbitMQ event broker. It processes the message, extracts the utility score and location data, and updates the dashboard's data store.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
	:lines: 22-35


The function ``update_fig`` is responsible for updating the dashboard's figure with the latest data. It creates a scatter plot of the utility scores and locations, allowing users to visualize the science event data in real-time.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 37-50

The function ``start_consumer`` is a blocking function that starts consuming messages from the RabbitMQ event broker.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 66-70

The code establishes a connection to the RabbitMQ event broker using the provided environment variables in a ``.env`` file. It uses the `pika` library to create a connection and a channel for publishing messages.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 74-92

After establishing the connection, the code defines and declares a RabbitMQ exchange named `science_event`. This exchange is used to route messages to the appropriate queues based on the routing key.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 94-96

The code then declares a queue and binds it to the `science_event` exchange. This queue will receive messages published by the Science Event Publisher.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 98-106

A basic consumer is then set up to listen for messages on the queue. When a message is received, it calls the `on_message` function to process the message and update the dashboard.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 110-113

A dataframe is created to store the utility scores and locations, which will be used to update the dashboard's figure.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 115-125

Finally, the code sets up the Dash application layout and starts the consumer in a separate thread to allow the dashboard to run concurrently with message consumption.

.. literalinclude:: /../../examples/scienceDash/scienceEventDashboard.py
   :lines: 127-

Execution
---------

The Science Event Dashboard Test Suite runs outside of the NOS-T tools library, so it does not use the standard NOS-T YAML configuration file. Instead, it requires a custom environment file (``.env``) to configure the RabbitMQ event broker connection.

Setting Up Environment File
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For this test suite, you will need to use an IDE to create a file with the
name ``.env`` containing the following information:

::

  HOST="your event broker host URL"
  PORT="your connection port"
  USERNAME="your event broker username"
  PASSWORD="your event broker password"

If you are running the test suite on your local computer using a local RabbitMQ event broker, you can set up the ``.env`` file like this:

::

   HOST="localhost"
   PORT=5672
   USERNAME="admin"
   PASSWORD="admin"

.. note::

  For details on setting up a local RabbitMQ broker, refer to the :ref:`localBroker` guide.

Executing the Science Event Dashboard Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, run each application on separate computers or consoles using the following commands: 

1. Run the Dashboard application:

   .. code-block:: bash

      python3 scienceEventDashboard.py

2. Run the Publisher application:

   .. code-block:: bash

      python3 scienceEventPublisher.py

Wherever the dashboard application is running, you should be able to see the utility scores
from a web browser (default address:  http://127.0.0.1:8050/). If everything is
running properly the dashboard will look like the figure below:

.. image:: media/scienceDash.png
   :width: 600
   :align: center

Conclusion
----------

This example demonstrates how to build a basic visualization tool using a pub/sub architecture with RabbitMQ, outside of the NOS-T Tools library. The Science Event Dashboard Test Suite provides a simple yet effective way to visualize science event data, helping users understand data flows and behaviors within a test suite.

Some good next steps for learning other NOS-T functions and developing your own test suites can be found at the following links:

* :ref:`Main Science Event Dashboard documentation <scienceDashEX>`
* :ref:`FireSat+ Test Suite <tutorial>`
* :ref:`Downlink Test Suite <downlinkTutorial>`
* :ref:`NOS-T Tools API documentation <nostTools>`