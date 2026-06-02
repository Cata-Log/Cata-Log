..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Configuration
=============

There are two parallel methods to configure your Cata-Log server.

Command-line
------------

Run

.. code-block:: console

    docker run dacid99/cata-log-hub:latest --help

or

.. code-block:: console

    python3 -m cata_log_hub --help

for an overview of the command line interface and the available options.

Environment
-----------

Instead of passing the options via the command line you can set them in the environment as well.

.. note::

    Settings via command line always override any environment configurations.

The names of the environment variables are the names of the corresponding cli options in UPPER_CAMEL_CASE with prefix *CATA_LOG_*.
So for example, *--request-timeout* becomes *CATA_LOG_REQUEST_TIMEOUT* .

This way of configuring Cata-Log is particularly useful in combination with docker.
The docker-compose.yml lists all available options with their defaults.
