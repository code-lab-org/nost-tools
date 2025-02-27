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

Pip Installation
----------------

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

Conda Installation
------------------

Installing Conda
^^^^^^^^^^^^^^^^

If you prefer using Conda for package and environment management but don't have it installed yet:

1. Download the Miniconda installer (recommended) from the `official site <https://docs.conda.io/en/latest/miniconda.html>`__:

   * **Linux**:
     ::
     
       wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
       bash Miniconda3-latest-Linux-x86_64.sh
     
   * **macOS**:
     ::
     
       wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
       bash Miniconda3-latest-MacOSX-x86_64.sh
     
   * **Windows**: Download the installer from the website and follow the graphical installation instructions

2. After installation, close and reopen your terminal or run:
   ::
   
     source ~/.bashrc  # Linux/macOS
   
3. Verify Conda is installed:
   ::
   
     conda --version

Installing NOS-T Tools
^^^^^^^^^^^^^^^^^^^^^^

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

Installing the Python Packages
------------------------------

Following the instructions above will automatically install the python packages that NOS-T depends on to run. These package dependencies can
otherwise be found in the `project specification <https://github.com/emmanuelgonz/nost-tools/blob/main/pyproject.toml>`__.

Next Step
---------

The publisher-subscriber example in the :ref:`publisher_subscriber_example` is a good next step to test the installation.