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

from cata_log.exceptions import PagesExhausted
from cata_log.utils import page_numbers
from cata_log.utils.dates import get_calendar_week_number

from .base import Preview, Provider
from .regions import Austria


class Hofer(Provider):
    """Provider class for Hofer current catalog."""

    uid = "hofer-au"
    name = "Hofer"
    url = "https://www.hofer.at/de/angebote/aktuelle-flugblaetter-und-broschuren.html"
    region = Austria
    description = "Hofer Prospekt"
    first_page_number = 0

    overview_url_format = "https://katalog.hofer.at/flipbook_kw{week_number:02}_{short_year}_0/spreads.json"
    base_url = "https://katalog.hofer.at"

    @override
    def _get_catalog_data(self) -> None:
        shifted_week_number = get_calendar_week_number(self._relevant_datetime) + (
            1 if self._relevant_datetime.weekday() >= Day.FRIDAY else 0
        )
        self.catalog_data = self._client.get(
            self.overview_url_format.format(
                week_number=shifted_week_number,
                short_year=self._relevant_datetime.year % 100,
            )
        ).json()

    @override
    def _get_page(self, page_number: page_numbers.PageNumber) -> bytes:
        double_page_number = page_number.as_double_page_number()
        try:
            image_url = self.catalog_data[double_page_number.number]["pages"][
                double_page_number.side
            ]["images"]["at2400"]
        except IndexError as error:
            raise PagesExhausted from error
        response = self._client.get(urljoin(self.base_url, image_url))
        return response.content

    @override
    def _get_valid_since(self) -> datetime:
        return datetime.combine(
            self._relevant_datetime
            - timedelta(days=self._relevant_datetime.weekday() - Day.FRIDAY + 7),
            time.min,
            self._relevant_datetime.tzinfo,
        )

    @override
    def _get_valid_until(self) -> datetime:
        return self._get_valid_since() + timedelta(days=7)


class HoferPreview(Preview, Hofer):
    """Provider class for Hofer preview catalog for next week."""

    uid = Hofer.uid + "-preview"
    name = Hofer.name + "-Vorschau"
    description = Hofer.description + " für nächste Woche"
    preview_timedelta = timedelta(days=7)
