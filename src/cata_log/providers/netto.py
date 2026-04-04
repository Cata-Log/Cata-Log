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

from celery.schedules import crontab

from cata_log.exceptions import PagesExhausted
from cata_log.utils import dates, page_numbers

from .base import Provider
from .regions import Germany


class Netto(Provider):
    """Provider class for Netto catalog."""

    name = "netto"
    description = "Netto Angebote"
    region = Germany
    url = "https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm"
    first_page_number = 0
    schedule = crontab(minute=0, hour=4, day_of_week="1-6")

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
            page_url = self.catalog_data[int(page_number)]["pages"][0]["images"][
                "at2400"
            ]
        except IndexError as error:
            raise PagesExhausted from error
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


class NettoPreview(Netto):
    """Provider class for Netto preview catalog for next week."""

    name = "netto-preview"
    description = Netto.description + " nächste Woche"
    schedule = crontab(minute=0, hour=4)

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=7)
