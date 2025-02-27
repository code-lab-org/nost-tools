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

*For instructions on how to install Conda, see the `Conda documentation <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__.*

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

Project Specifications
------------------------------

Following the instructions above will automatically install the python packages that NOS-T depends on to run. These package dependencies can
otherwise be found in the `project specification <https://github.com/emmanuelgonz/nost-tools/blob/main/pyproject.toml>`__.

Next Step
---------

The publisher-subscriber example in the :ref:`publisher_subscriber_example` is a good next step to test the installation.