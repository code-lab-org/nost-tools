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

Then, from a command prompt,  navigate to the root directory 
(the location where you cloned the library) and install by running the following command:

:: 
  
  pip install -e .

Installing the Python Packages
------------------------------

Following the instructions above will automatically install the python packages that NOS-T depends on to run. These package dependencies can
otherwise be found in the `requirements file <https://github.com/code-lab-org/nost-tools/blob/main/docs/requirements.txt>`__.

Next Step
---------

The Getting Started Guide is a simple test case which publishes 
utility scores to a dashboard. It is comprised of just two applications
and is a good place to start. For documentation, please see: :ref:`getStarted`.