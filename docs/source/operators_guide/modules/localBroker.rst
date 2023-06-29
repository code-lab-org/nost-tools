Setting up Solace Broker on Local Machine
=========================================

While there are many alternative broker implementation options available, NOS-T adopts the Solace PubSub+ Standard Edition event broker, a proprietary but freely available commercial product supporting up to 1000 concurrent connections and 10,000 messages per second. PubSub+ supports and interoperates among several protocols and several open protocols including Message Queuing Telemetry Transport (MQTT), Advanced Message Queuing Protocol (AMQP), and Representational State Transfer (REST). All protocols share similar messaging constructs but exhibit some minor differences in implementation and library availability. The testbed is currently designed to use strictly the MQTT protocol, but the capability of Solace to handle other protocols lends itself to future extensibility.

This page shows how to configure a new standalone Solace broker on a local machine. The tutorial mostly mirrors the SolaceLabs `solace-single-docker-compose <https://github.com/SolaceLabs/solace-single-docker-compose>`_ project which provides instructions and tools to get a single Solace PubSub+ software message broker Docker container up-and-running on a desktop using Docker Compose, a tool for defining and running multi-container Docker applications.  While the capabilities of a locally hosted broker are more limited, it is useful for becoming familiar with the Solace interface and experimenting with publisher/subscriber behaviors.

Initializing a Solace Event Broker with Docker Compose
------------------------------------------------------

This tutorial specifically makes use of a Docker container for setting up the broker. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries and settings. In order to use the Docker Compose commands described, one of the following can be installed:

	* `Docker Desktop for Windows <https://docs.docker.com/desktop/install/windows-install/>`_ with at least 2 GiB of memory dedicated to Docker Engine.
	
	* `Docker Desktop for Mac <https://docs.docker.com/desktop/install/mac-install/>`_ with at least 2 GiB of memory dedicated to Docker Engine.
	
	* `Docker Desktop for Linux <https://docs.docker.com/desktop/install/linux-install/>`_ with at least 2 GiB of memory dedicated to Docker Engine.
	
Each of the latter includes the Docker Compose tool. To check if Docker Compose is running correctly, open an elevated command prompt and enter the following:

>>> docker-compose --help

If a list of options or commands is not displayed, then `installing Docker Compose directly <https://docs.docker.com/compose/install/>`_ may be necessary.

To begin setting up a broker, clone the Solace git repository for the `solace-single-docker-compose <https://github.com/SolaceLabs/solace-single-docker-compose>`_. By cloning this repository, any updates made by Solace can be easily integrated to ensure broker compliance. Alternatively, the `PubSubStandard_singleNode.yml <https://github.com/SolaceLabs/solace-single-docker-compose/blob/37cba15c4ee6a2ce402c699a93560f4a14335e75/template/PubSubStandard_singleNode.yml>`_ file can be downloaded directly for local use, but without the benefit of syncing to the managed git repository. Open an elevated command prompt and change directories to the location of this :obj:`.yml` and enter the following:

.. code-block:: console
	
	>>> docker-compose -f PubSubStandard_singleNode.yml up -d
	[+] Running 2/2
	- Volume "template-storage-group"	Created							##.#s
	- Container pubSubStandardSingleNode	Started							##.#s
   
If actively running the Docker Desktop client, the Containers tab should include a single container called **template**. Expanding the **template** container shows a single active node:

.. image:: Docker_Desktop_Containers.png
	:width: 800

Similarly, the Volumes tab should include a single, in-use **template_storage-group**:
	
.. image:: Docker_Desktop_Volumes.png
	:width: 800
	
Note that the names of both the container and the storage-group can be customized by editing the :obj:`.yml` file accordingly.

Logging into the Solace Event Broker
------------------------------------

Coming soon.

Customizing your Solace Event Broker
------------------------------------

Coming soon.

Clients
^^^^^^^

Coming soon.

Queues
^^^^^^

Coming soon.

Access Control
^^^^^^^^^^^^^^

Coming soon.

Cache
^^^^^

Coming soon.


