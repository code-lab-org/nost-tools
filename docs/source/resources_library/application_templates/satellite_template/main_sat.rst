.. _satBaseMain:

main_sat.py
===========

Of the four scripts that make up the Basic Satellite template, this is the "entry point," the one that you need to execute. It uses functions and parameters in the other files to simulate the satellite. 

The following code also demonstrates how the ground application is started up and how the :obj:`Satellite` and :obj:`StatusPublisher` object classes are initialized and added to the simulator. It also adds the :obj:`ShutDownObserver` from the :ref:`Application Objects  <toolsAppObj>` in the :ref:`NOS-T Tools Library <nostTools>`.

.. literalinclude:: /../../examples/application_templates/satellite_template/main_sat.py
	:lines: 18-

