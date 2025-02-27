.. _installation:

NOS-T Tools Installation
========================

The best way to get the NOS-T tools library and example codes is to clone the NOS-T git repository
and install the tools. There are several ways to clone a git repository. `Here <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository?tool=webui>`__
is a good description of some of these methods.

Cloning the Repository
----------------------

1. Clone the repository:

  ::

    git clone git@github.com:emmanuelgonz/nost-tools.git

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

Dependencies and Requirements
------------------------------

The installation process automatically handles all required dependencies for NOS-T tools. These include:

- Core libraries for messaging and event processing
- Utilities for simulation integration
- Network communication components

For a complete list of dependencies and version requirements, refer to the `project specification file (pyproject.toml) <https://github.com/emmanuelgonz/nost-tools/blob/main/pyproject.toml>`__ in the repository.

If you encounter any compatibility issues, ensure you're using Python 3.9 or newer, as this is the recommended version range for NOS-T tools.

Next Steps
----------

**Important:** NOS-T requires an event broker to function. To get started:

1. Set up a local RabbitMQ broker: :ref:`localBroker` guide. Alternatively, you can use a cloud-based broker by checking in with the NOS-T operator.
2. Verify your installation by testing the publisher-subscriber example: :ref:`publisher_subscriber_example`

These steps will ensure your environment is correctly configured and ready for developing with NOS-T.