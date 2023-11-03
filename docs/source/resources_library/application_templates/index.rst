.. _appTemplates:

Application Templates
=====================

This section contains templates for common NOS-T applications. These applications will function together and are based on the :ref:`FireSat+ NOS-T example test Suite <fireSatExampleTop>`.

These applications contain the scaffolding for a test suite so that users do not have to start from scratch. However, the NOS-T infrastructure is very flexible and most of the design choices for these applications are unnecessary. Some examples of these choices are storing credentials in .env files or defining parameters in a config file. 

.. toctree::
   :maxdepth: 2

   satellite_template/modules
   ground_station_template/modules
   random_global_event_template/modules
   manager_template/modules