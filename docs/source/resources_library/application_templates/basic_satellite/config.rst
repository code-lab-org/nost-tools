.. _satBaseConfig:

config.py
=========

The configuration file contains most of the parameters required to define the spacecraft. These could be hardcoded within the other scripts that make up the Basic Satellite Template, however it is a good practice to keep these in an accessible place changes can be made easily and consistently. Currently, the important information contained in the config.py file include the prefix for the channel that the Satellite will publish its messages to, and parameters regarding the timing of your scenario.

.. literalinclude:: /../../examples/application_templates/basic_satellite/config.py
	:lines: 9-