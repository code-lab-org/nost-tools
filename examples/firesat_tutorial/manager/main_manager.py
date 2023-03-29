# -*- coding: utf-8 -*-
"""
    *This application demonstrates a manager synchronizing a test case between disaggregated applications*

    This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :obj:`ManagedApplication` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.

    .. literalinclude:: /../../examples/firesat/manager/main_manager.py
    	:lines: 12-

"""
