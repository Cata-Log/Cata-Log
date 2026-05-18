..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Troubleshooting
===============

This is a curated list of issues that may arise when hosting or using Cata-Log.

After setting up my Cata-Log instance, I can't access the webinterface or authenticate any API requests.
--------------------------------------------------------------------------------------------------------

You most likely forgot to set a password.

Cata-Log has no default password, barring any logins.

Just set your own with the --password cli option or the CATA_LOG_PASSWORD environment variable.

I have set an environment variable to configure Cata-Log but it doesn't take effect.
------------------------------------------------------------------------------------

First of all double-check that the variable starts with *CATA_LOG_* and is a UPPER_CAMEL_CASE version of a command-line option.

If that is the case you are probably also setting that command-line option, which overrides the environment setting.

For the docker image the host and port settings are not available as they are needed to correctly expose the Cata-Log server inside the container.
