.. _instructionsScienceDash:

Science Event Dashboard Step-by-Step Instructions
=================================================

The Science Event Dashboard Test Suite is a simple example of NOS-T
capabilities. It does not require the use of the NOS-T tools library.
It contains two applications, a Science Event Publisher which regularly publishes
the utility score and random location for science events distributed globally.
The second application is a basic dashboard which publishes the utility and 
location with the Python Dash library.

In order to run the Science Event test case you first need to get the two
applications which comprise this test suite from the project git at
`[this link] <https://github.com/code-lab-org/nost-tools/tree/main/examples/scienceDash>`_

Initial requirements
--------------------

This test suite assumes that you have first followed the installation
instructions.


Setting up environment files
----------------------------

In order to protect your (and our) information, these applications use an
environment file for usernames, passwords, event broker host site URLs, and
port numbers.

For this test suite you will need to use a text editor to create a file with the
name ".env" containing the following text. Make sure that you "Save as type"
"All files" and *not* as a text file. 

::

  HOST="your event broker host URL"
  PORT=#### - your connection port
  USERNAME="your event broker username"
  PASSWORD="your event broker password"

Each application must have this file in the home path. If they're both in the
same folder then just one is sufficient.

Running a test case
-------------------

Next, run each application on separate computers or consoles. Wherever the
dashboard application is running, you should be able to see the utility scores
from a web browser (default address:  http://127.0.0.1:8050/). If everything is
running properly it will look like below:

.. image:: media/scienceDash.png
   :width: 600
   :align: center
