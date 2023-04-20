.. _satBaseConfig:

config.py
=========

The configuration file contains most of the parameters required to define the spacecraft. These could be hardcoded within the other scripts that make up the Basic Satellite Template, however it is a good practice to keep these in an easily accessible place so you don't forget to make changes when you want. Currently, the important information contained in the config.py file include the prefix for the channel that the Satellite will publish its messages to, and parameters regarding the timing of your scenario.

.. literalinclude:: /../../examples/satBaseClass/config.py
	:lines: 9-