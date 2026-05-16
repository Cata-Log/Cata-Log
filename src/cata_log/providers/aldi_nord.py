# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Cata-Log - the central hub for grocery store catalogs
# Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from calendar import Day
from datetime import datetime, time, timedelta
from typing import override

from cata_log.utils import dates, page_numbers

from .base import Preview, Provider
from .regions import Germany


class AldiNord(Provider):
    """Provider class for AldiNord catalog."""

    uid = "aldi-nord-de"
    name = "Aldi-Nord"
    description = "Aldi-Nord Angebote"
    region = Germany
    url = "https://www.aldi-nord.de/prospekte/"
    first_page_number = 1
    schedule = "0 4 * * *"

    page_url_format = "https://ipaper.ipapercms.dk/aldi-nord/aldi-aktuell/{valid_since:%Y}/{valid_since:%Y}cw{week_number:02}mopromotionaldi-angebote-ab-montag-{valid_since:%d}-{valid_since:%m}-1/Image.ashx?PageNumber={page_number}&ImageType=Normal"

    @override
    def _get_catalog_data(self) -> None:
        pass

    @override
    def _get_page(self, page_number: page_numbers.PageNumber) -> bytes:
        return self._client.get(
            self.page_url_format.format(
                valid_since=self.get_valid_since(),
                week_number=dates.get_calendar_week_number(self._relevant_datetime),
                page_number=int(page_number),
            )
        ).content

    @override
    def _get_valid_since(self) -> datetime:
        return datetime.combine(
            self._relevant_datetime
            - timedelta(days=self._relevant_datetime.weekday() - Day.MONDAY),
            time.min,
            self._relevant_datetime.tzinfo,
        )

    @override
    def _get_valid_until(self) -> datetime:
        return self._get_valid_since() + timedelta(days=7)


class AldiNordPreview(Preview, AldiNord):
    """Provider class for AldiNord preview catalog for next week."""

    uid = AldiNord.uid + "-preview"
    name = AldiNord.name + "-Vorschau"
    description = AldiNord.description + " nächste Woche"
    schedule = "0 4 * * *"
    preview_timedelta = timedelta(days=7)
