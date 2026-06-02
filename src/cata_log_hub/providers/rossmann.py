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

import httpx
from httpx import HTTPStatusError

from cata_log_hub.exceptions import CatalogUnavailableWarning
from cata_log_hub.utils.dates import get_calendar_week_number
from cata_log_hub.utils.page_numbers import PageNumber

from .base import Provider
from .regions import Germany


class RossmannBeilage(Provider):
    """Provider class for Rossmann Beilage catalog."""

    uid = "rossmann-beilage-de"
    name = "Rossmann-Angebote"
    description = "Rossmann Angebote"
    url = "https://www.rossmann.de/de/kataloge/angebote/index.html"
    region = Germany
    schedule = "0 5 * * 1-5"

    url_format = "https://www.rossmann.de/de/kataloge/angebote/catalogs/{relevant_datetime:%Y}_kw{week_number}_beilage/normal/bk_{page_number}.jpg"

    @override
    def _get_catalog_data(self) -> None:
        pass

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        try:
            response = self._client.get(
                self.url_format.format(
                    relevant_datetime=self._relevant_datetime,
                    week_number=get_calendar_week_number(self._relevant_datetime),
                    page_number=page_number,
                ),
            )
        except HTTPStatusError as status_error:
            if (
                status_error.response.status_code == httpx.codes.NOT_FOUND
                and page_number == self.first_page_number
            ):
                raise CatalogUnavailableWarning from status_error
            raise
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


class RossmannAktion(RossmannBeilage):
    """Provider class for Rossmann Angebote catalog."""

    uid = "rossmann-aktion-de"
    name = "Rossmann-Aktionsangebote"
    description = "Rossmann Aktionsangebote"

    url_format = "https://www.rossmann.de/de/kataloge/angebote/catalogs/{relevant_datetime:%Y}_kw{week_number}_aktion/normal/bk_{page_number}.jpg"
