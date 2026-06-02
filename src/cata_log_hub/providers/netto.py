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
from urllib.parse import urljoin

from cata_log_hub.exceptions import PagesExhausted
from cata_log_hub.utils import dates, page_numbers

from .base import Preview, Provider
from .regions import Germany


class Netto(Provider):
    """Provider class for Netto catalog."""

    uid = "netto-de"
    name = "Netto"
    description = "Netto Angebote"
    region = Germany
    url = "https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm"
    first_page_number = 0
    schedule = "0 4 * * 1-6"

    overview_url_format = (
        "https://wochenprospekt.netto-online.de/hz{week_number}_pobd/spreads.json"
    )
    base_url = "https://wochenprospekt.netto-online.de"

    @override
    def _get_catalog_data(self) -> None:
        self.catalog_data = self._client.get(
            self.overview_url_format.format(
                week_number=dates.get_calendar_week_number(self._relevant_datetime),
            )
        ).json()

    @override
    def _get_page(self, page_number: page_numbers.PageNumber) -> bytes:
        try:
            page_data = self.catalog_data[int(page_number)]
        except IndexError as error:
            raise PagesExhausted from error
        page_url = page_data["pages"][0]["images"]["at2400"]
        return self._client.get(urljoin(self.base_url, page_url)).content

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


class NettoPreview(Preview, Netto):
    """Provider class for Netto preview catalog for next week."""

    uid = Netto.uid + "-preview"
    name = Netto.name + "-Vorschau"
    description = Netto.description + " nächste Woche"
    schedule = "0 4 * * *"

    @override
    def _get_preview_timedelta(self) -> timedelta:
        return timedelta(days=7)
