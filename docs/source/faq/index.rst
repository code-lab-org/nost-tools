Frequently Asked Questions (FAQ)
===============================

This section addresses common questions about the NOS Testbed (NOS-T).

General Questions
---------------

What is NOS-T?
^^^^^^^^^^^^^
NOS-T (New Observing Strategies Testbed) is a digital engineering environment developed by NASA to facilitate the development, testing, and evaluation of new observing strategies for space missions.

Who can use NOS-T?
^^^^^^^^^^^^^^^^
NOS-T is available to NASA personnel, contractors, academic partners, and other authorized users working on relevant projects. Contact the NOS-T team for access information.

Is NOS-T open source?
^^^^^^^^^^^^^^^^^^
Parts of the NOS-T toolkit are open source. Please refer to the repository license for specific details on usage and distribution.

Technical Questions
-----------------

What computing resources are required?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
NOS-T can run on standard workstations for basic simulations. More complex modeling may require high-performance computing resources. See the installation guide for specific requirements.

Can NOS-T interface with other simulation tools?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Yes, NOS-T is designed with an interoperability framework that allows integration with various external tools and models. See the API documentation for details.

What messaging protocol does NOS-T use?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
NOS-T uses the Advanced Message Queuing Protocol (AMQP) for communication between distributed simulation components. AMQP is an open standard application layer protocol for message-oriented middleware focused on reliability, security, and interoperability.

Do I need to understand AMQP to use NOS-T?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A deep understanding is not necessary to start using NOS-T. However, familiarity with basic concepts like brokers, exchanges, queues, and bindings will help you work more effectively with the system. See the :doc:`../operators_guide/modules/amqpProtocol` section for more details.

Where is the NOS-T broker hosted?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The NOS-T broker is hosted on an Amazon Elastic Compute Cloud (EC2) instance. Connection details are provided during the onboarding process.

Troubleshooting
-------------

Simulation crashes with memory error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This typically occurs when running complex scenarios on insufficient hardware. Try reducing the simulation fidelity or using a machine with more RAM.

Cannot connect to distributed simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Check your network configuration and firewall settings. The distributed simulation features require specific ports to be open. See the network configuration guide.

Messages aren't being received by components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Verify that your exchanges and queues are properly bound with correct routing keys. Check that publishers and consumers are using matching exchange types and binding patterns.

Getting Additional Help
--------------------

If your question isn't answered here, consider:

* Checking the detailed documentation sections
* Posting in the user forum
* Submitting a GitHub issue
* Contacting the NOS-T support team:
   * PI: Paul T. Grogan, `paul.grogan@asu.edu <mailto:paul.grogan@asu.edu>`_
   * Research Scientist: Emmanuel M. Gonzalez, `emmanuelgonzalez@asu.edu <mailto:emmanuelgonzalez@asu.edu>`_