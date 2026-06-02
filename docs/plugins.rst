..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Plugins
=======

Cata-Log has a plugin system for providers.

This allows you to use providers that are not built-in or use your own custom implementations.

Activation
----------

Activating a plugin is straightforward.

1. Get a file for a Cata-Log plugin. A plugin file must end in *.py*.
   It must contain at least one class that inherits from *cata_log_hub.providers.base.Provider*.

.. important::

    Please be careful what files you use as plugins!
    They may potentially include malicious code that will be executed on your machine if used as a plugin.

2. Put the file in the */mnt/plugins/* docker volume or the plugin directory of the cata_log_hub server.
You may order the plugins files into subdirectories within these directories.

3. Restart (or start) the Cata-Log instance. The plugged-in provider is now available.

Deactivation
------------

To deactivate a plugin:

1. Remove the plugin from the */mnt/plugins/* docker volume or the provider directory of the cata_log_hub server.

2. Restart (or start) the Cata-Log instance. The plugged-in provider will be gone.

.. note::

    If you have a provider that uses the removed plugin, its catalog will no longer be cached and it will be marked as misconfigured.
    Catalogs that are already cached will still be available though.
