.. _installation:

NOS-T Tools Installation
========================

The best way to get the NOS-T tools library and example codes is to clone the NOS-T git repository
and install the tools. There are several ways to clone a git repository. `Here <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository?tool=webui>`__
is a good description of some of them.

Cloning the Repository
----------------------

First, you need to clone the repository from the following link:

https://github.com/code-lab-org/nost-tools

Installing NOS-T tools requires pip version 23 or greater. Install via

::
  
  python -m pip install --upgrade pip

Then, from a command prompt,  navigate to the root directory (the location where you cloned the library) and install by running the following command:

:: 
  
  pip install -e .

If you want to install additional libraries required to run the examples, run:

:: 
  
  pip install -e .[examples]


Installing the Python Packages
------------------------------

Following the instructions above will automatically install the python packages that NOS-T depends on to run. These package dependencies can
otherwise be found in the `project specification <https://github.com/code-lab-org/nost-tools/blob/main/pyproject.toml>`__.

Next Step
---------

The hands-on tutorial will walk you through the FireSat+ test suite and is a good next step. It 
starts with the installation process given here and continues with a :ref:`tutorialSystemDescription`.