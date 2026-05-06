..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Installation
============

There are two ways to install Cata-Log:

Docker
======

Follow these steps to set up your instance of Cata-Log:

1. Get `the docker-compose.yml file <https://gitlab.com/cata-log/cata-log/-/blob/main/docker/docker-compose.yml>`_ from the git repository.
2. Adapt it to your needs. For details on the environment variables, refer to :doc:`the configuration page <configuration>`.
3. Deploy the stack any way you wish. Common options are via the command-line

   .. code-block:: console

      docker compose up -d

   or with a container manager like `portainer <https://www.portainer.io/>`_, `dockge <https://dockge.kuma.pet/>`_ or many others.
4. Open *<server_ip>:2424* to check whether the container started successfully.

.. important::

    If you want to access Cata-Log from outside your private network, please reverse-proxy.
    The basic HTTP authentication that Cata-Log uses is highly insecure without https!

Bare-Metal
==========

Follow these steps to set up your instance of Cata-Log:

1. Install cata_log from PyPI

    ```bash
    pip install cata_log
    ```

2. Start the server with

    ```bash
    python3 -m cata_log
    ```

3. Open *<server_ip>:8000* to check whether the container started successfully.

.. important::

    If you want to access Cata-Log from outside your private network, please reverse-proxy.
    The basic HTTP authentication that Cata-Log uses is highly insecure without https!
