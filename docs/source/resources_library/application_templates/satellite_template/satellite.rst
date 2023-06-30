.. _satBaseSatellite:

satellite.py
============

The template contains two classes, the :obj:`Satellite` (:obj:`Entity`) object class and the one :obj:`StatusPublisher` (:obj:`WallclockTimeIntervalPublisher`) class. Both :obj:`Entity` and :obj:`WallclockTimeIntervalPublisher` come from the :ref:`NOS-T Tools Library <nostTools>`. They are found, respectively in the :ref:`Simulator Objects <toolsSimObj>` and :ref:`Application Objects <toolsAppObj>` sections.

The template also adds several methods within these classes. The classes have built-in methods that are unique to each object. The :obj:`Satellite` class tracks state transitions for the satellite, while the :obj:`StatusPublisher` standardizes the message structure and frequency of published messages updating these states.

Satellite
---------

.. autoclass:: examples.application_templates.satellite_template.satellite.Satellite
	:show-inheritance:

.. automethod:: examples.application_templates.satellite_template.satellite.Satellite.initialize

.. automethod:: examples.application_templates.satellite_template.satellite.Satellite.tick

.. automethod:: examples.application_templates.satellite_template.satellite.Satellite.tock

Status Publisher
^^^^^^^^^^^^^^^^

.. autoclass:: examples.application_templates.satellite_template.satellite.StatusPublisher
	:show-inheritance:

.. _satTemplateView:

Instrument View and Interfacing with the Ground Station Template
----------------------------------------------------------------

This satellite template is very basic. The :ref:`example codes <examples>` contain satellite scripts that have extended functionality. In particular, some useful functions are to see where on the Earth's surface is in view of an instrument, and when the spacecraft is able to communicate with a ground station. The following code snippet from the :ref:`FireSat+ test suite <fireSatConstellations>` contains methods that can perform these functions. Combining the :obj:`check_in_view` and :obj:`check_in_range` methods allows for simulating ground communciations with the :ref:`Ground Station Template <groundTemplate>`. Further discussion on all of these methods is found in the :ref:`Hand-on Tutorial Satellites section <tutorialSat>`.

*NOTE*: If you wish to add functions to the satellite template, remember to add the relevant data to the message that :ref:`main_sat.py <satBaseMain>` publishes, and the structure for that data to the :ref:`schemas.py <satBaseSchemas>`.

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 39-159