Plugins
=======

Cata-Log has a plugin system for providers.

This allows you to use providers that are not built-in or use your own custom implementations.

Installation
------------

Installation of a plugin is straightforward.

1. Get a file for a Cata-Log plugin. A plugin file must end in *.py*. It must contain at least one class that inherits from *cata_log.providers.base.Provider*.

.. important::

    Please be careful what files you use as plugins!
    They may potentially include malicious code that will be executed on your machine if used as a plugin.

2. Put the file in the */mnt/plugins/* docker volume.
You may order the plugins into subdirectories of that volume.

3. Restart (or start) the Cata-Log instance. The plugged-in provider is now available.

Uninstallation
--------------

To uninstall a plugin:

1. Remove the plugin from the */mnt/plugins/* docker volume.

2. Restart (or start) the Cata-Log instance. The plugged-in provider will be gone.

.. note::

    If you have a provider that uses the removed plugin, its catalog will no longer be cached and it will be marked as misconfigured.
    Catalogs that are already cached will still be available though.
