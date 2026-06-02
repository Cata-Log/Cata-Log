..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

How To Create A Plugin
======================

If you want to create and use a new providerplugin, you need to implement a new provider class.

First you need to create a new file for the plugin `<plugin_name>.py`.
It is important that the file has the extension *.py*.

Writing the code for the plugin provider is analogous to writing a provider.
Please refer to :doc:`the guide on creating a provider <how-to-add-provider>` for a full explanation.

.. important::

    There is one important difference between a built-in provider and a plugin:

    A plugin must use full imports from `cata_log_hub.providers` while a built-in provider can import from `.` .

    Provider:

        .. code-block:: python

            from .base import Provider

    Plugin:

        .. code-block:: python

            from cata_log_hub.providers.base import Provider

After you have written the code for the plugin, you can test it manually by adding it to your local Cata-Log instance.

See :doc:`the plugin instruction <plugins>` for more details on how to do that.
