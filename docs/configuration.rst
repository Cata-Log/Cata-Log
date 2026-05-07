..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Configuration
=============

There are two ways to configure Cata-Log.

Command-line
------------

Run

.. code-block:: console

    docker run dacid99/cata-log:latest --help

for an overview of the command line interface and the available options.

.. note::

    Settings via command line always override any environment configurations.


Environment
-----------

Instead of passing the options via the command line you can set them in the environment as well.

The names of the environment variables are the names of the corresponding cli options in uppercase with a prefix *CATA_LOG_*.

This way of configuring Cata-Log is particularly useful in combination with docker.
The docker-compose.yml lists the various available options with their defaults.
