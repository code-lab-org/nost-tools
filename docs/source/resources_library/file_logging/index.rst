.. _fileLogging:

File Logging
============

As of version 2.4.0, NOS-T supports automatic file logging for all application types. When enabled, log messages are written to rotating log files in addition to the console.

Overview
--------

The ``configure_file_logging()`` method in the ``Application`` class sets up a ``RotatingFileHandler`` that writes log messages to disk. This method is automatically called during ``start_up()`` when ``enable_file_logging`` is set to ``True`` in the YAML configuration.

YAML Configuration
------------------

File logging is configured through the ``LoggingConfig`` fields, which are inherited by ``ManagerConfig`` and ``ManagedApplicationConfig``:

.. code-block:: yaml

   execution:
     manager:
       enable_file_logging: True       # Enable file logging (default: False)
       log_dir: "logs"                 # Directory for log files (default: "logs")
       log_filename: "manager.log"     # Log filename (default: auto-generated with timestamp)
       log_level: "DEBUG"              # Log level: DEBUG, INFO, WARNING, ERROR (default: "INFO")
       max_bytes: 10485760             # Max file size before rotation (default: 10 MB)
       backup_count: 5                 # Number of backup files to keep (default: 5)
       log_format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"  # Log format string

     managed_applications:
       my_app:
         enable_file_logging: True
         log_dir: "logs"
         log_level: "INFO"

**Fields:**

- ``enable_file_logging``: Set to ``True`` to enable file logging. Default: ``False``.
- ``log_dir``: Directory where log files are created. Created automatically if it does not exist. Default: ``"logs"``.
- ``log_filename``: Name of the log file. If not provided, a timestamped filename is generated automatically.
- ``log_level``: Minimum log level to capture. Default: ``"INFO"``.
- ``max_bytes``: Maximum size of each log file in bytes before rotation. Default: 10 MB.
- ``backup_count``: Number of rotated backup log files to retain. Default: 5.
- ``log_format``: Python logging format string. Default: ``"%(asctime)s [%(levelname)s] %(name)s: %(message)s"``.

Programmatic Configuration
--------------------------

You can also call ``configure_file_logging()`` directly on any application instance:

.. code-block:: python

   from nost_tools.application import Application

   app = Application(app_name="my_app")

   app.configure_file_logging(
       log_dir="logs",
       log_filename="my_app.log",
       log_level="DEBUG",
       max_bytes=5 * 1024 * 1024,  # 5 MB
       backup_count=3,
   )

Parameters passed to this method override any values from the YAML configuration. If a parameter is ``None``, the value from the YAML configuration (or the default) is used.
