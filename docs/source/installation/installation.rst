.. _installation:

Installation
============

The installation phase involves:

1. Installing the NOS-T Tools library
2. Cloning the NOS-T tools repository
3. Configuring the necessary credentials to interact with the NOS-T infrastructure


Integrated Development Environment
----------------------------------

.. start-ide-installation

An Integrated Development Environment (IDE) will make developing applications and interacting with NOS-T much easier. Below is a list of recommended IDEs:

- `Visual Studio Code (VS Code) <https://visualstudio.microsoft.com/>`__: Lightweight, highly customizable, supports many languages via extensions.
- `IntelliJ IDEA <https://www.jetbrains.com/idea/>`__: Excellent for Java and Kotlin, with strong support for other JVM languages.
- `Eclipse <https://eclipseide.org/>`__: Popular for Java development, also supports C/C++, Python, and more.
- `PyCharm <https://www.jetbrains.com/pycharm/>`__: Feature-rich Python IDE by JetBrains, great for web development and data science.

.. note:: 
  Users are encouraged to use `VS Code <https://visualstudio.microsoft.com/>`__ due to its lightweight design, ease of setup, and strong community support. It also offers built-in support for Jupyter notebooks, making it especially helpful for getting started with NOS-T development.
|

.. end-ide-installation

NOS-T Tools Installation
------------------------

.. start-nos-t-installation

The NOS-T Tools library is available on `PyPi <https://pypi.org/project/nost-tools/>`__ and can be installed using ``pip``, the standard package manager for Python or ``conda``. Below are the instructions for both methods.

Pip 
^^^

To install NOS-T tools using ``pip``, follow these steps:

1. Upgrade ``pip`` to the latest version:

.. code-block:: bash
    
    python -m pip install --upgrade pip

2. Install NOS-T Tools:

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

.. note:: 
  Following the instructions above will install the Python packages that the test suite depends on to run. The details of these dependencies, including version numbers, can
  otherwise be found in the `requirements file <https://github.com/code-lab-org/nost-tools/blob/main/pyproject.toml>`__.
|

.. end-nos-t-installation

Repository Cloning
------------------

.. start-repository-cloning

The recommended way to access the example code is by cloning the NOS-T Tools repository from GitHub. If you're unfamiliar with how to clone a Git repository, you can find detailed instructions `here <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository?tool=webui>`__.

Clone the repository:
::
  git clone git@github.com:code-lab-org/nost-tools.git

If the above fails, you can also try the HTTPS version:
::
  git clone https://github.com/code-lab-org/nost-tools.git

.. end-repository-cloning

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

.. important::

    Restart your computer after defining environmental variables in your ~/.bashrc file.

Dependencies and Requirements
------------------------------

NOS-T Tools has several dependencies that are essential for its functionality.

.. seealso::

    For a complete list of dependencies and version requirements, refer to the `project specification file (pyproject.toml) <https://github.com/code-lab-org/nost-tools/blob/main/pyproject.toml>`__ in the repository.

Below is a categorized list of these dependencies, including both core and optional libraries:

Core Dependencies
^^^^^^^^^^^^^^^^^

The core dependencies include essential libraries required for the basic functionality of NOS-T Tools:

- Core libraries for messaging, event processing, and authentication

  - `pika <https://pypi.org/project/pika/>`__, `python-keycloak <https://pypi.org/project/python-keycloak/>`__

- Time synchronization utilities 

  - `ntplib <https://pypi.org/project/ntplib/>`__

- Data serialization and validation tools

  - `pydantic <https://pypi.org/project/pydantic/>`__

- Data manipulation libraries

  - `numpy <https://pypi.org/project/numpy/>`__, `pandas <https://pypi.org/project/pandas/>`__

- Configuration and environment management utilities

  - `python-dotenv <https://pypi.org/project/python-dotenv/>`__, `pyyaml <https://pypi.org/project/pyyaml/>`__


Optional Dependencies
^^^^^^^^^^^^^^^^^^^^
NOS-T Tools also supports several optional dependencies that enhance its functionality for specific use cases. These dependencies can be installed as needed.

Examples
""""""""

The ``examples`` optional dependencies include additional libraries for running example applications including:
  
- Visualization tools
  
  - `matplotlib <https://pypi.org/project/matplotlib/>`__, `dash <https://pypi.org/project/dash/>`__, `seaborn <https://pypi.org/project/seaborn/>`__

- Geospatial libraries
  
  - `geopandas <https://pypi.org/project/geopandas/>`__, `rioxarray <https://pypi.org/project/rioxarray/>`__, `shapely <https://pypi.org/project/shapely/>`__

- Data formats

  - `netCDF4 <https://pypi.org/project/netCDF4/>`__, `h5netcdf <https://pypi.org/project/h5netcdf/>`__, `h5py <https://pypi.org/project/h5py/>`__

- Optimization tools
  
  - `PuLP <https://pypi.org/project/PuLP/>`__
  
- Cloud storage
  
  - `s3fs <https://pypi.org/project/s3fs/>`__, `boto3 <https://pypi.org/project/boto3/>`__

To install the optional dependencies for examples:

.. code-block:: bash

    python3 -m pip install "nost_tools[examples]"  # For example applications

Development
"""""""""""

The ``dev`` optional dependencies include additional libraries for development and testing including:
  
- `black <https://pypi.org/project/black/>`__, `pytest <https://pypi.org/project/pytest/>`__, `pylint <https://pypi.org/project/pylint/>`__, `coverage <https://pypi.org/project/coverage/>`__

To install the optional dependencies for development:
.. code-block:: bash

    python3 -m pip install "nost_tools[dev]"  # For development tools

Documentation
"""""""""""""

The ``docs`` optional dependencies include additional libraries for building documentation including:

- `sphinx <https://pypi.org/project/Sphinx/>`__, `autodoc_pydantic <https://pypi.org/project/autodoc_pydantic/>`__, `sphinx_rtd_theme <https://pypi.org/project/sphinx_rtd_theme/>`__

To install optional dependencies for documentation:

.. code-block:: bash

    python3 -m pip install "nost_tools[docs]"      # For documentation building



.. note::

    If you encounter compatibility issues, check your Python version (3.8+) and ensure your environment meets all requirements.

Next Steps
----------

**Important:** NOS-T requires an event broker to function. To get started:

1. Set up a local RabbitMQ broker: :ref:`localBroker` guide. Alternatively, you can use a cloud-based broker by checking in with the NOS-T operator.
2. Verify your installation by testing the publisher-consumer example: :ref:`publisher_consumer_example`

These steps will ensure your environment is correctly configured and ready for developing with NOS-T.