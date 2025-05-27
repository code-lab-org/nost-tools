.. _installation:

Installation
============

The installation phase involves:

1. Cloning the NOS-T tools repository
2. Installing the NOS-T Tools library
3. Configuring the necessary credentials to interact with the NOS-T infrastructure.


NOS-T Tools Installation
------------------------
To install the NOS-T tools library, you can use either ``pip`` or ``conda``. Below are the instructions for both methods.

Pip 
^^^

To install NOS-T tools using ``pip``, follow these steps:

1. Upgrade `pip`` to the latest version:

.. code-block:: bash
    
    python -m pip install --upgrade pip

2. Install NOS-T tools:

.. code-block:: bash
    
    python3 -m pip install nost-tools

To install additional libraries required to run the NOS-T Tools examples:

.. code-block:: bash
    
    python3 -m pip install "nost_tools[examples]"

Conda
^^^^^

*For instructions on how to install Conda, see the:* `Conda documentation <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__.

To install NOS-T tools using conda:

1. Create a new conda environment (recommended):

.. code-block:: bash

    conda create -n nost python=3.11
    conda activate nost

2. Install NOS-T tools:

.. code-block:: bash
    
    python3 -m pip install nost-tools

To install additional libraries required to run the examples:

.. code-block:: bash

    python3 -m pip install "nost_tools[examples]"

Credentials
-----------

Credentials required by the NOS-T infrastructure can be defined in your bashrc file or using a .env file.

Bashrc
^^^^^^

Open your bashrc file:

.. code-block:: bash

    vim ~/.bashrc

Add the following lines:

.. code-block:: bash

    export USERNAME=<NOS-T Keycloak Username>
    export PASSWORD=<NOS-T Keycloak Password>
    export CLIENT_ID=<Ask NOS-T Operator>
    export CLIENT_SECRET_KEY=<Ask NOS-T Operator>

Source the changes:

.. code-block:: bash

    source ~/.bashrc

.env
^^^^

You can create a .env file using the same values as listed above:

.. code-block:: bash

    vim .env

Add the following lines:

.. code-block:: bash

    USERNAME=<NOS-T Keycloak Username>
    PASSWORD=<NOS-T Keycloak Password>
    CLIENT_ID=<Ask NOS-T Operator>
    CLIENT_SECRET_KEY=<Ask NOS-T Operator>

.. note::

    Restart your computer after defining environmental variables in your ~/.bashrc file.

Dependencies and Requirements
------------------------------

NOS-T tools requires Python 3.8 or newer. The installation process automatically handles all required dependencies.

**Core Dependencies:**

- Core libraries for messaging, event processing, and authentication (pika, python-keycloak)
- Time synchronization utilities (ntplib)
- Data serialization and validation tools (pydantic)
- Data manipulation libraries (numpy, pandas)
- Configuration and environment management utilities (python-dotenv, pyyaml)

**Optional Dependencies:**

- **examples:** Additional libraries for running example applications including:
  
  - Visualization tools (matplotlib, dash, seaborn)
  - Geospatial libraries (geopandas, rioxarray)
  - Data formats (netCDF4, h5netcdf)
  - Optimization tools (pulp)
  - Cloud storage (s3fs, boto3)
  
- **dev:** Additional libraries for development and testing including:

  - Development tools (black, pytest, pylint, coverage)
  
- **docs:** Additional libraries for building documentation including:

  - Documentation tools (sphinx, autodoc_pydantic, sphinx_rtd_theme)

To install optional dependencies:

.. code-block:: bash

    python3 -m pip install "nost_tools[examples]"  # For example applications
    python3 -m pip install "nost_tools[dev]"       # For development tools
    python3 -m pip install "nost_tools[docs]"      # For documentation building

For a complete list of dependencies and version requirements, refer to the `project specification file (pyproject.toml) <https://github.com/code-lab-org/nost-tools/blob/main/pyproject.toml>`__ in the repository.

If you encounter compatibility issues, check your Python version (3.8+) and ensure your environment meets all requirements.

Next Steps
----------

**Important:** NOS-T requires an event broker to function. To get started:

1. Set up a local RabbitMQ broker: :ref:`localBroker` guide. Alternatively, you can use a cloud-based broker by checking in with the NOS-T operator.
2. Verify your installation by testing the publisher-consumer example: :ref:`publisher_consumer_example`

These steps will ensure your environment is correctly configured and ready for developing with NOS-T.