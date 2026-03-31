.. _authModes:

Authentication Modes
====================

NOS-T supports three authentication modes for connecting to the RabbitMQ message broker. The mode is automatically detected based on the credentials provided in the ``.env`` file and the ``keycloak_authentication`` setting in the YAML configuration.

Overview
--------

.. list-table::
   :widths: 25 25 25 25
   :header-rows: 1

   * - Mode
     - Use Case
     - Required Credentials
     - ``keycloak_authentication``
   * - Basic Auth
     - Localhost / development
     - ``USERNAME`` + ``PASSWORD``
     - ``False``
   * - Keycloak Service Account
     - Automated systems, scripts
     - ``CLIENT_ID`` + ``CLIENT_SECRET_KEY``
     - ``True``
   * - Keycloak User Account
     - Interactive users with OTP/2FA
     - ``USERNAME`` + ``PASSWORD`` + ``CLIENT_ID`` + ``CLIENT_SECRET_KEY``
     - ``True``

Basic Auth (Localhost/Development)
----------------------------------

For local development with a RabbitMQ broker that does not use Keycloak, only a username and password are required.

**YAML configuration:**

.. code-block:: yaml

   servers:
     rabbitmq:
       keycloak_authentication: False
       host: "localhost"
       port: 5672
       tls: False
       virtual_host: "/"

**.env file:**

.. code-block:: bash

   USERNAME="admin"
   PASSWORD="admin"

This mode connects directly to RabbitMQ using the provided credentials without any OAuth2/JWT token exchange.

Keycloak Service Account
------------------------

For automated systems, scripts, and long-running processes that authenticate using client credentials only (no interactive user login required).

**YAML configuration:**

.. code-block:: yaml

   servers:
     rabbitmq:
       keycloak_authentication: True
       host: "nost.smce.nasa.gov"
       port: 5671
       tls: True
       virtual_host: "/"
     keycloak:
       host: "nost.smce.nasa.gov"
       port: 8443
       tls: True
       token_refresh_interval: 240
       realm: "NOS-T"

**.env file:**

.. code-block:: bash

   CLIENT_ID="your-client-id"
   CLIENT_SECRET_KEY="your-client-secret"

The system uses ``grant_type=client_credentials`` to obtain an access token from Keycloak. No username, password, or OTP is required.

Keycloak User Account
---------------------

For interactive users who authenticate with their Keycloak credentials. This mode supports OTP/2FA when configured in Keycloak.

**YAML configuration:** Same as Service Account (above).

**.env file:**

.. code-block:: bash

   USERNAME="your-username"
   PASSWORD="your-password"
   CLIENT_ID="your-client-id"
   CLIENT_SECRET_KEY="your-client-secret"

The system uses ``grant_type=password`` with the provided username and password. If the Keycloak realm requires OTP/2FA, the system will detect this and prompt for a one-time password.

**OTP handling:**

- The system analyzes Keycloak error responses for OTP-related keywords (``otp``, ``totp``, ``two-factor``, ``2fa``, ``mfa``).
- Only prompts for OTP when Keycloak explicitly indicates it is required.
- Provides clear error messages for different failure scenarios (wrong password vs. OTP required vs. expired OTP).

For programmatic OTP support, pass the ``otp`` parameter to ``new_access_token()``:

.. code-block:: python

   app.new_access_token(otp="123456")

Credentials Validation
----------------------

The ``Credentials`` schema validates that the provided credential combination matches one of the three supported modes. Invalid combinations (e.g., only a ``USERNAME`` without a ``PASSWORD``, or a ``CLIENT_ID`` without a ``CLIENT_SECRET_KEY``) will raise a ``ValidationError`` with a message listing the valid authentication modes.

For the full setup guide for Keycloak and RabbitMQ OAuth2 integration, see :doc:`AMQP with Keycloak <amqp_keycloak>`.
