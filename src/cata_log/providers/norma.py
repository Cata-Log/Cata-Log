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

from cata_log.utils.dates import get_calendar_week_number
from cata_log.utils.page_numbers import PageNumber

from .base import Preview, Provider
from .regions import Germany


class Norma(Provider):
    """Provider class for Norma catalog."""

    name = "Norma"
    description = "Norma Angebote"
    region = Germany
    url = "https://www.norma-online.de/de/angebote/onlineprospekt/"

    catalog_url_format = "https://www.norma-online.de/de/angebote/online-prospekt/{year}-{week_number:02}_FG/files/page/{page_number}.jpg"

    @override
    def _get_catalog_data(self) -> None:
        pass

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        response = self._client.get(
            url=self.catalog_url_format.format(
                year=self._relevant_datetime.year,
                week_number=get_calendar_week_number(
                    self._relevant_datetime, self.region.week_counting_startpoint
                ),
                page_number=page_number,
            ),
        )
        return response.content

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


class NormaPreview(Preview, Norma):
    """Provider class for Norma preview catalog for next week."""

    name = Norma.name + "-Vorschau"
    description = Norma.description + " nächste Woche"
    preview_timedelta = timedelta(days=7)


class NormaPrepreview(NormaPreview):
    """Provider class for Norma preview catalog for second-next week."""

    name = Norma.name + "-Vorvorschau"
    description = Norma.description + " übernächste Woche"
    preview_timedelta = timedelta(days=14)


class NormaRetrospect(NormaPreview):
    """Provider class for Norma retrospect catalog for last week."""

    name = Norma.name + "-Rückschau"
    description = Norma.description + " letzte Woche"
    preview_timedelta = -timedelta(days=7)


class NormaRetrospect2(NormaPreview):
    """Provider class for Norma retrospect catalog for second-last week."""

    name = Norma.name + "-Rückrückschau"
    description = Norma.description + " vorletzte Woche"
    preview_timedelta = -timedelta(days=14)
