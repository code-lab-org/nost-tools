.. _operatorsGuide:

Operator's Guide
================

A basic requirement for NOS-T is having access to a message broker. This guide is meant to aid someone who needs to set up a message broker and coordinate communication between multiple clients.

.. toctree::
   :maxdepth: 1

   modules/mqttProtocol
   modules/localBroker
   
*NOTE:* This guide follows specific choices for a working testbed architecture, but many of these choices could be replaced by alternatives with similar functional capability. For example, NOS-T adopts the Solace PubSub+ Standard Edition event broker, but there are many other event broker products available that can also facilitate event-driven architectures. Similarly, Amazon Web Services (AWS) were chosen for hosting a cloud-based event broker, but other service providers and products may also satisfy the requirements for a cloud-based testbed architecture.