.. _satBaseConfig:

config.py
=========

The configuration file contains most of the parameters required to define the spacecraft. These could be hardcoded within the other scripts that make up the Basic Satellite Template, however it is a good practice to keep these editable variables in an accessible place where changes can be made easily and consistently. Currently, the important information contained in the config.py file include the :obj:`PREFIX` for the channel that the Satellite will publish its messages to, parameters regarding the timing of your scenario. The :obj:`PREFIX` is currently set to :obj:`template`, you will need to have this value set consistently among your constituent applications.

The other important parameter that you can change is the :obj:`name`. The :obj:`name`, currently :obj:`SUOMI NPP`, will pull a spacecraft's current TLEs from `Celestrak <https://celestrak.com/NORAD/elements/active.txt>`_ to model the orbit.

.. literalinclude:: /../../examples/application_templates/satellite_template/config.py
	:lines: 9-