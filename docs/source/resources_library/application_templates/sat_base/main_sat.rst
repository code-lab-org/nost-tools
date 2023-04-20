main_sat.py
===========

Of the four scripts that make up the Basic Satellite template, this is the one that you need to execute. It uses functions and parameters in the the other files to simulate the satellite. Important parameters that you can change are the :obj:`name` and :obj:`field_of_regard`. The :obj:`name`, currently :obj:`SUOMI NPP` below, will pull a spacecraft's current TLEs from `Celestrak <https://celestrak.com/NORAD/elements/active.txt>`_. The :obj:`field_of_regard` affects the viewable area of the Earth's surface at any one time.

The following code also demonstrates how the ground application is started up and how the :obj:`Satellite` and :obj:`StatusPublisher` object classes are initialized and added to the simulator. It also adds the :obj:`ShutDownObserver` from the :ref:`NOS-T Tools Library <nostTools>`.

.. literalinclude:: /../../examples/satBaseClass/main_sat.py
	:lines: 18-

