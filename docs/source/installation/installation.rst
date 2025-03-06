.. _installation:

Installation
============

The installation phase involves: 
1. Cloning the NOS-T tools repository
2. Installing the NOS-T Tools library
3. Configuring the necessary credentials to interact with the NOS-T infrastructure.

.. note::

    The best way to get the NOS-T Tools library and example codes is to clone the NOS-T git repository 
    and install the tools. The library will soon be available on PyPI for easy installation.

Cloning the Repository
----------------------

1. Clone the repository:

  ::

    git clone git@github.com:emmanuelgonz/nost-tools.git

  If the above command fails, try using the HTTPS URL instead:

  ::

    git clone https://github.com/emmanuelgonz/nost-tools.git

2. Change to the directory where the repository was cloned:

  ::

    cd nost-tools

NOS-T Tools Installation
------------------------

Pip 
^^^

To install NOS-T tools using pip:

1. Upgrade pip to the latest version:

  ::
    
    python -m pip install --upgrade pip

2. Install NOS-T tools:

  :: 
    
    pip install .

To install additional libraries required to run the examples:

  :: 
    
    pip install .[examples]

Conda
^^^^^

*For instructions on how to install Conda, see the:* `Conda documentation <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__.

To install NOS-T tools using conda:

1. Create a new conda environment (recommended):

  ::

    conda create -n nost python=3.11
    conda activate nost

2. Install NOS-T tools:

  :: 
    
    pip install .

To install additional libraries required to run the examples:

  :: 
    
    pip install .[examples]

Credentials
-----------

Credentials required by NOS-T can be defined in your bashrc file or using a .env file.

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

The installation process automatically handles all required dependencies for NOS-T tools. These include:

- Core libraries for messaging and event processing
- Utilities for data processing of NetCDF and HDF5 files
- Libraries for plotting and data analysis

For a complete list of dependencies and version requirements, refer to the `project specification file (pyproject.toml) <https://github.com/emmanuelgonz/nost-tools/blob/main/pyproject.toml>`__ in the repository.

If you encounter any compatibility issues, ensure you're using Python 3.9 or newer, as this is the recommended version range for NOS-T tools.

Next Steps
----------

**Important:** NOS-T requires an event broker to function. To get started:

1. Set up a local RabbitMQ broker: :ref:`localBroker` guide. Alternatively, you can use a cloud-based broker by checking in with the NOS-T operator.
2. Verify your installation by testing the publisher-consumer example: :ref:`publisher_consumer_example`

These steps will ensure your environment is correctly configured and ready for developing with NOS-T.