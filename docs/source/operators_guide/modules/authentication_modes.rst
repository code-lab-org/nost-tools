.. _authModes:

Authentication Modes
====================

NOS-T supports four authentication modes for connecting to the RabbitMQ message broker. The first three are automatically detected based on the credentials provided in the ``.env`` file and the ``keycloak_authentication`` setting in the YAML configuration. The fourth (pre-acquired tokens) is selected by passing tokens directly to ``start_up()`` and is intended for server-side components acting on behalf of an already-authenticated end user.

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
   * - Keycloak Pre-acquired Tokens
     - Server-side delegation (act on behalf of an authenticated user)
     - ``CLIENT_ID`` + ``access_token`` + ``refresh_token`` (passed to ``start_up()``)
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

Keycloak Pre-acquired Tokens
----------------------------

For server-side components (e.g., a backend API) that receive tokens from an already-authenticated end user and need to act on behalf of that user against RabbitMQ. In this mode, ``nost_tools`` does not perform a Keycloak grant itself; instead, it uses tokens obtained elsewhere (typically forwarded from a frontend that completed an Authorization Code flow).

This preserves per-user RabbitMQ scope enforcement end-to-end: every publish performed by the server-side ``Application`` or ``Manager`` is authenticated with the original user's token, so RabbitMQ's OAuth2 plugin applies the user's group-based permissions (e.g., ``rabbitmq.configure:*/sos*/sos*``) to each operation.

**YAML configuration:** Same as Service Account (above).

**.env file:**

.. code-block:: bash

   CLIENT_ID="nost_monitor_nodejs"

Set ``CLIENT_ID`` to the Keycloak client that originally issued the forwarded tokens (the refresh endpoint requires the ``client_id`` to match). For public clients, ``CLIENT_SECRET_KEY`` is not required. ``USERNAME`` and ``PASSWORD`` are not used in this mode.

**Usage:**

Pass the forwarded tokens as keyword arguments to ``start_up()``:

.. code-block:: python

   manager = Manager()
   manager.start_up(
       prefix="my_scenario",
       config=config,
       access_token=user_access_token,
       refresh_token=user_refresh_token,
   )

The background refresh thread renews the session by calling Keycloak's refresh endpoint with the provided refresh token on the normal ``token_refresh_interval`` cadence, so long-running scenarios (hours, days, or longer — bounded by Keycloak's SSO session settings) remain continuously authenticated without further action from the caller.

**Requirements:**

- Both ``access_token`` and ``refresh_token`` must be provided. Passing ``access_token`` alone raises ``ValueError`` at startup, because the refresh thread cannot keep the session alive without a refresh token.
- The Keycloak client identified by ``CLIENT_ID`` must permit refresh via ``grant_type=refresh_token`` (default for public clients issued via Authorization Code flow).
- The user whose tokens are forwarded must have whatever RabbitMQ scopes the scenario requires, projected into the token's ``extra_scope`` claim through the usual Keycloak mapper configuration.

Credentials Validation
----------------------

The ``Credentials`` schema validates that the provided credential combination matches one of the three supported modes. Invalid combinations (e.g., only a ``USERNAME`` without a ``PASSWORD``, or a ``CLIENT_ID`` without a ``CLIENT_SECRET_KEY``) will raise a ``ValidationError`` with a message listing the valid authentication modes.

For the full setup guide for Keycloak and RabbitMQ OAuth2 integration, see :doc:`AMQP with Keycloak <amqp_keycloak>`.
