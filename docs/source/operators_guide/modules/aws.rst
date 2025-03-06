AWS CLI
=======

As NOS-T operator, it may be necessary to use Amazon Web Services (AWS) resources. To facilitate that this documentation will walk you through the process of setting up the AWS command line interface (CLI).

.. note::
    
    Once you have installed and configured the AWS CLI, you can use it to interact with AWS services directly from the command line. Additionally, you can use the Python SDK, boto3, to programmatically interact with AWS services. Note that boto3 requires the AWS CLI to be installed and properly configured to function correctly.

Installation
------------

Installation instructions are provided below. For further information on AWS CLI installation, `click here <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>`__.

Linux
^^^^^

.. code-block:: bash

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install

Windows
^^^^^^^

1. Download and run the AWSL CLI installer: 

.. code-block:: powershell

    msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

1. Confirm successful installation

.. code-block:: powershell

    aws --version

Mac
^^^

1. Download AWS CLI installer:

.. code-block:: bash

    curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

1. Run the installer: 

.. code-block:: bash

    sudo installer -pkg ./AWSCLIV2.pkg -target /

1. Confirm successful installation:

.. code-block:: bash

    aws --version

Configuration
-------------

Once installed, the AWS CLI must be configured:

.. code-block:: bash

    aws configure

You will be prompted for the following information:

1. AWS Access Key ID
2. AWS Secret Access Key
3. Default region name
4. Default output format

.. note::

    Enter the Access Key ID and Secret Access Key provided by the NOS-T operator. The default region name and output format can be left blank.

These credentials will be stored in the `~/.aws/credentials` file.