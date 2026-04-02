..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

How To Add A New Region
=======================

If your region is not yet implemented in cata-log, feel invited to add it yourself!

This is a straightforward task, here is a list of what to do with a full example:

1. Add a new class inheriting from the Region baseclass to src/cata_log/providers/regions.py.

2. Add all metadata as required by the baseclass.

    - local_name: The name of the region in the language of the region.
    - language_code: The IANA code for the language of the region. Just look it up in `the complete list <https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes>`_.
    - timezone: The timezone of the region.
    - week_counting_startpoint: The day weeks are counted from in the region. Either Monday or Sunday.

    .. code-block:: python

        class ExampleRegion(Region):
            """Example region class."""

            local_name = "ekzemplo"
            language_code = "eo"
            timezone = zoneinfo.ZoneInfo("Europe/Warsaw")
            week_counting_startpoint = WeekCountingStartpoints.MONDAY


3. Commit and send a merge-request. Done!
