..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Installation
============


Basic Setup
-----------

There are two main roads to installing Cata-Log:

Docker
^^^^^^

Follow these steps to set up your instance of Cata-Log:

1. Get `the docker-compose.yml file <https://gitlab.com/cata-log/cata-log/-/blob/main/docker/docker-compose.yml>`_ from the git repository.
2. Adapt it to your needs. For details on the environment variables, refer to :doc:`the configuration page <configuration>`.
   Don't forget to set *CATA_LOG_PASSWORD*, otherwise you won't be able to log in.
3. Deploy the stack any way you wish. Common options are via the command-line

   .. code-block:: console

      docker compose up -d

   or with a container manager like `portainer <https://www.portainer.io/>`_, `dockge <https://dockge.kuma.pet/>`_ or many others.
4. Open *<server_ip>:2424* to check whether the container started successfully.

Bare-Metal
^^^^^^^^^^

Follow these steps to set up your instance of Cata-Log:

1. Install cata_log from PyPI

    ```bash
    pip install cata_log
    ```

2. Start the server with

    ```bash
    python3 -m cata_log --password=<your_password>
    ```

    Don't forget to set a password, otherwise you won't be able to log in.

3. Open *<server_ip>:8000* to check whether the container started successfully.

.. important::

    If you want to access Cata-Log from outside your private network, please reverse-proxy.
    The basic HTTP authentication that Cata-Log uses is highly insecure without https!

Further Configuration
---------------------

You can refine the upper basic setup to match your use case.

External Database
^^^^^^^^^^^^^^^^^

Cata-Log uses an internal sqlite3 database by default.
This works fine but has some deficits in terms of concurrency and thread-safety.

If you can please follow the next steps to use an external full-fledged database server instead.

You can pass the URL of a database either by command-line or environment option to be used instead of the internal sqlite database.

.. note::

    You can use a database that is also used by another application.
    For example if you deploy Cata-Log in the same environment (machine or docker stack) as a shopping-list server,
    you can simply make Cata-Log use the same database container as the main service.
    The two services and their data will not interfere with each other.

Available options are:

- MySQL:

.. code-block:: text

    mysql+pymysql://<db_username>:<db_password>@<database_ip>:<database_port>/cata-log

- PostgreSQL:

.. code-block:: text

    postgresql+pg8000://<db_username>:<db_password>@<database_ip>:<database_port>/cata-log

.. important::

    Make sure to use the complete protocol with the driver as given in these templates.

You can use the docker-compose files for both setups as reference.

Configuration
^^^^^^^^^^^^^

Your instance can be configured in many details.

Refer to :doc:`the configuration page <configuration>` for all details.
