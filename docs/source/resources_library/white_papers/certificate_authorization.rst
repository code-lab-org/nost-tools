.. _certAuth:

Configuring Client Certificates with the Solace Broker
======================================================

This guide provides a step-by-step method for authorizing broker clients. This will aid in ensuring that your communications over the broker are secure.


Creating and Configuring Broker 
-------------------------------

This guide assumes that you have created a solace docker container, and the following ports are mapped: 

8080 (insecure manager access) 

1943 (secure manager access) 

8883 (MQTT with TLS) 

8443 (MQTT over WebSockets with TLS) 

Next, you need to obtain a SSL certificate from a trusted authority and upload it to the broker as the server certificate. This must be done through the Solace CLI. 

Additionally, you must enable Client Certificate Authentication on the broker by going to Access Control > Client Authentication > Settings, and switching “Client Certificate Authentication” to on. Also ensure that “Username Source” is set to Common Name. 

To add usernames of clients, navigate to Access Control > Client Usernames, and add as many client usernames as necessary. To ensure clients without enabled usernames can not connect even if they have a trusted certificate, disable the “default” client username. 


Creating Certificate Authority (CA)
-----------------------------------

For clients to authenticate with the broker, they must have a certificate signed by an authority trusted by the broker, and the Common Name (CN) of the certificate must match a username in the broker. It is possible to aquire client certificates that are signed by a trusted authority, but these are expensive and inconvienent. Free certificate services such as LetsEncrypt only offer server certificates, not client certificates. Standard practice for these types of applications is for the broker manager to create their own CA and generate certificates for users. This requires the CA to be added to the list the broker trusts. 

To generate a Certificate Authority to sign client certificates, ensure OpenSSL is installed and enter the following commands: 

To generate the CA's private key:

.. code-block::

    openssl genrsa -des3 -out root.key 4096

You will need to input a password that will be required to sign certificates in the future using this CA. 

To generate the CA's public certificate: 

.. code-block::

    openssl req -new -x509 -days 365 -key root.key -out root.pem 

Where the number after days (365 above) is the length of time the certificate is valid for. You will be prompted for several parameters that can be stored within the certificate, including: 

* Country Name (2 letter code)
* State or Province Name (full name) 
* Locality Name (eg, city) 
* Organization Name (eg, company) 
* Organizational Unit Name 
* Common Name (e.g. server FQDN or YOUR name) 
* Email Address 

These fields are all optional except for CN, which should just be whatever you want the CA to be called. 

This Authority is not trusted by the broker by default, so the certificate must be added to the broker in order for certificates signed by it to be trusted. To do this, enter the following command to examine the CA certificate: 

.. code-block::

    openssl x509 -in root.pem -text 

From this command's output, copy the section beginning with ``-----BEGIN CERTIFICATE-----`` and ending with ``-----END CERTIFICATE-----`` including those lines to the clipboard. 

Now go to the broker manager, navigate to User Mgmt > User Authentication > Client Certificate Authorities and click “+ Client Certificate Authority”.  Give it a name and click “Change Certificate” at the bottom of the settings, and paste the certificate you copied earlier into the text box. Apply the changes. 

Generating Client Certificates 
------------------------------

For users to obtain a certificate to validate their clients, they must generate their own private key and certificate signing request, and give the signing request to the manager of the certificate authority made above. 

To generate a private key: 

.. code-block::
    
    openssl genrsa -out username.key 4096 

To generate certificate signing request: 

.. code-block::

    openssl req -new -key username.key -out username.csr 

Again, the user will be prompted with the same parameters as when generating the CA's certificate. Fill in as many as you want, but the one that is important is CN as the name input for this must match a username added to the solace broker. The user can now send this .csr file to the person managing the CA to sign. 

To sign the request an issue a certificate, the CA manager must input the following command: 

.. code-block::

    openssl x509 -req -days 365 -in username.csr -CA root.pem -CAkey root.key -CAcreateserial -out username.pem 

This will ask for the password used when first creating the CA private key. This username.pem is the user's public certificate, and can now be sent back to them to be used in their applications. 

There is likely a relatively simple way to automate this process, but when you have few users, manual distribution of certificates should not be too cumbersome.  

Using Client Certificates 
-------------------------

To use the certifcates in python applications, all that needs to be done is include a filepath to your certificate and key in your application's :ref:`.env file <envSetUp>`, and then pass these paths to the ``ConnectionConfig`` object used to start the application. This is identical to how username and password were passed to the broker previously. Username and password are no longer necessary, and are not parameters of the ``ConnectionConfig`` object. 

To use the certificates in javascript applications such as Cesium dashboards, the certificate isn't passed to the javascript code, it is uploaded directly to the browser. To do this, you must first combine your certificate and private key into one pkcs12 format file. Use the following command to do this: 

.. code-block::

    openssl pkcs12 -inkey username.key -in username.pem -export -out username.pfx 

This will prompt you for a password, which must be entered again when uploading to your browser. 

To upload your certificate to the browser: 

Navigate to “Settings > Privacy & Security > Security,  and then select “View Certificates”, and under “Your Certificates” select “Import” and navigate to the .pfx file created in the previous step. You will be prompted for the password used when you created that file. 

The above instructions are specifically for Mozilla Firefox, but the steps are mostly identical for other browsers. 

Now that your certificate is uploaded to the browser, the first time you connect to the broker with a web application, you will be prompted to choose a certificate to offer the broker to authenticate you. Choose the one you just uploaded, and when you connect in the future it will choose this one automatically.  