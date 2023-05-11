config.py
=========

The NOS-T manager configuration file contains a few parameters important for test case execution. First, the :obj:`PREFIX`, currently configured as :obj:`"template"` sets which topic the manager will publish its command messages to. You *must* ensure that any managed applications in your test case are using the same :obj:`PREFIX` otherwise they will never start up.