.. _satBaseConfig:

config.py
=========

The configuration file contains most of the parameters required to define the spacecraft. These could be hardcoded within the other scripts that make up the Basic Satellite Template, however it is a good practice to keep these editable variables in an accessible place where changes can be made easily and consistently. Currently, the important information contained in the config.py file include the :obj:`PREFIX` for the channel that the Satellite will publish its messages to, parameters regarding the timing of your scenario, and :obj:`GROUND` parameters defining a (currently unused - coming soon) ground station.

Other important parameters that you can change are the :obj:`name` and :obj:`field_of_regard`. The :obj:`name`, currently :obj:`SUOMI NPP` below, will pull a spacecraft's current TLEs from `Celestrak <https://celestrak.com/NORAD/elements/active.txt>`_. The :obj:`field_of_regard` affects the viewable area of the Earth's surface at any one time.

.. literalinclude:: /../../examples/application_templates/satellite_template/config.py
	:lines: 9-