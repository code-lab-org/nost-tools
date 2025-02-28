.. _operatorsGuide:

Operator's Guide
================

Introduction
-----------
This guide serves as a comprehensive resource for system operators deploying and managing the New Observing Strategies Testbed (NOS-T). In the NOS-T ecosystem, an "operator" is responsible for establishing and maintaining the underlying infrastructure that enables effective simulation and testing across distributed systems.

Purpose
-------
The primary objective of this guide is to provide detailed instructions for:

* Setting up and configuring the message broker infrastructure
* Establishing reliable communication channels between distributed clients
* Managing message routing and system topology
* Monitoring system performance and troubleshooting common issues
* Scaling resources according to simulation complexity and participant requirements

Core Requirements
----------------
A fundamental requirement for NOS-T is a properly configured message broker that facilitates the exchange of information between simulation components. This guide walks through the entire process from initial setup to advanced configuration, ensuring your testbed meets the necessary performance and reliability standards for mission-critical simulations.

Contents
--------

.. toctree::
   :maxdepth: 2

   modules/amqp
   modules/yml_file

Implementation Notes
-------------------
*NOTE:* This guide presents a specific reference architecture for a functional testbed environment, but many components can be substituted with alternatives offering similar capabilities. For example:

* NOS-T adopts RabbitMQ as its event broker, but other AMQP-compliant brokers may be suitable alternatives.
* Amazon Web Services (AWS) is featured for cloud-based deployments, but other cloud providers (Microsoft Azure, Google Cloud Platform) or on-premises solutions can be configured to satisfy testbed requirements.
* The configuration patterns demonstrated are optimized for space mission simulation but can be adapted for other distributed system testing scenarios.

Following this guide will enable you to establish a robust infrastructure foundation for NOS-T, ensuring reliable communication, appropriate security controls, and scalable performance for your simulation needs.