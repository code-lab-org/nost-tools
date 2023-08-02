.. _cloudBroker:

Setting up AWS Cloud-Hosted NOS-T Event Broker
==============================================

A message broker only provides value if applications are able to connect to them, and thus setting up a :ref:`Local Broker<localBroker>` has limited usefulness. This section covers how to set up a cloud-based message broker. The NOS-T message broker has been set up on an AWS Elastic Compute Cloud (EC2) instance on NASA's Science Managed Cloud Environment (SMCE), so many of the instructions will be specific to Amazon Web Services. A message broker could similarly be hosted by other cloud computing services, but the instructions and nomenclature may vary.

Launching a New EC2 Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once logged into the AWS console, navigate to the EC2 dashboard and select **Launch instances**. This will open a prompt for choosing an Amazon Machine Image for the basis of the instance. 

Amazon Machine Engine (AMI)
---------------------------

This choice will vary depending on the use-case and specific security needs, but NOS-T uses the Red Hat Enterprise Linux 9.

.. image:: RedHat.png
	:width: 800
	:align: center
	
|

Instance Type and Configurations
--------------------------------

Once a base image is chosen, it must be paired with an instance type. This will vary depending on the amount of activity expected on the instance, and also may depend on user cost constraints given the on-demand pricing per hour of instance operation. NOS-T currently operates on a **t3a.large** instance. 

Storage requirements and constraints must also be considered. The EC2 instance hosting the NOS-T broker currently operates with a volume of 40 GiB.


Key-Pairs and Security Settings
-------------------------------

Key-pairs are required for operators to regularly monitor and connect to the instance. Key-pair names are often chosen with a convention like {operator_last_name}-{project_name} for traceability.

Security groups have proven essential for the development team to manage access to the broker. The EC2 instance that hosts the NOS-T message broker is protected by firewall, and access is granted via white-listed IP addresses.

When setting up a security group, the operator must define which ports will be open. This depends on protocols used for communication. For NOS-T we open the following ports:

	*	**22:** Secure Shell Protocol (SSH)
	*	**8883:** MQTT Default VPN over Transport Layer Security (TLS)
	*	**8443:** MQTT Default VPN over WebSockets / TLS
	*	**9443:** REpresentational State Transfer (REST) default VPN over TLS
	*	**1443:** Web transport over Transport Layer Security (TLS)
	*	**1943:** Solace Element Management Protocol (SEMP) over TLS
	*	**8080:** SEMP/PubSub+ Manager (see :ref:`Logging into the Solace Event Broker<PubSubManager>`)
	*	**55443:** Solace Message Format (SMF) over TLS
	
Once the configurations and security groups are set, select **Launch Instances**. The operator will be prompted for an existing key-pair or to download a new key-pair for secure connection to the instance. This key-pair file should have a *.pem* extension. 

Once the instance is launched, it will be assigned a Public IPv4 address. It is recommended that operators assign an Elastic IP address to the EC2 instance, as public IP addresses may change if and when machines are disconnected and reconnected.

PuTTY
^^^^^

PuTTY is a free and open-source terminal emulator, serial console and network file transfer application. It supports many protocols, but for set up we will just use PuTTY for SSH communication.

PuTTYgen
--------

Before communicating via SSH, the operator must convert the latter discussed key-pair file with the *.pem* extension to a private key with a *.ppk* extension using the PuTTYgen tool. In the PuTTY Configuration menu, navigate to the SSH Auth submenu. Browse and select the *.ppk* file just saved.

.. image:: Putty_Auth_Credentials.png
	:width: 400
	:align: center
	
|

PuTTY Configuration
-------------------

Now that the certificate with the private key is loaded, navigate to the Session menu.

.. image:: Putty_Session.png
	:width: 500
	:align: center
	
|

Under **Host Name** use the default username ec2-user@{Public_IPv4_address}. The Public IPv4 address can be found under the **Details** tab for the corresponding EC2 instance.

Since this session will be necessary to reconnect from time to time, it is useful to save the session with a unique name that can be selected from a drop-down list.  The first time you connect, you will be prompted that "The server's host key is not cached in the registry." If you trust the host is the correct one, select Accept and you should not see this prompt again.


PuTTY Session
-------------

The first step once connected is ensure that all installed packages and their dependencies on a Linux system are up to date, which is accomplished with the following command:

>>> sudo yum update -y

After updates complete, the most recent Docker Engine package should be installed:

>>> sudo amazon-linux-extras install docker

Once installed, the Docker service must be started:

>>> sudo service docker start

Now that the Docker service is started, add the :obj:`ec2-user` to the :obj:`docker` group so you can execute Docker commands without using :obj:`sudo`.

>>> sudo usermod -a -G docker ec2-user

Note that after changing the group, the operator may need to disconnect and reconnect the PuTTY Session to make sure Docker is running, which the operator can check with the following command:

>>> docker info

Most instances of an event broker will require TLS encryption. Setting up this encryption first requires navigating back to the Inbound Rules for the security group and opening up Port **80** (set Source Type to Anywhere-IPv4).

Next, because we are using a Linux 2 AMI, we will also need to allow installations from the Extra Packages for Enterprise Linux Repository (EPEL):

>>> sudo amazon-linux-extras install epel

Now that the instance has access to this repository, the operator can install CertBot:

>>> sudo yum install -y certbot

After completion, run the following command:

>>> sudo certbot certonly --standalone

CertBot will prompt the operator to provide a contact email address and ask you to accept terms of use. Subsequently, CertBot will prompt the operator for the domain name. Once entered, the server is verified 




	