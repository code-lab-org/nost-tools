.. _installation:

NOS-T Tools Installation
========================

The best way to get the NOS-T tools library and example codes is to clone the NOS-T git repository
and install the tools. There are several ways to clone a git repository. `Here <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository?tool=webui>`__
is a good description of some of these methods.

Pip Installation
-----------------------

For development purposes or to access the latest code and examples, clone the repository and install in development mode:

1. Clone the repository:

::

  git clone git@github.com:emmanuelgonz/nost-tools.git

2. Upgrade pip to the latest version:

::
  
  python -m pip install --upgrade pip

3. Install NOS-T tools:

:: 
  
  pip install .

To install additional libraries required to run the examples:

:: 
  
  pip install .[examples]

Conda Installation
----------------

To install NOS-T tools using conda:

1. Clone the repository:

::

  git clone git@github.com:emmanuelgonz/nost-tools.git

2. Create a new conda environment (recommended):

   ::
   
     conda create -n nost python=3.11
     conda activate nost

3. Install NOS-T tools using pip within the conda environment:

   ::
   
     pip install .[examples]

Installing the Python Packages
------------------------------

Following the instructions above will automatically install the python packages that NOS-T depends on to run. These package dependencies can
otherwise be found in the `project specification <https://github.com/emmanuelgonz/nost-tools/blob/main/pyproject.toml>`__.

Next Step
---------

The publisher-subscriber example in the :ref:`publisher_subscriber_example` is a good next step to test the installation.