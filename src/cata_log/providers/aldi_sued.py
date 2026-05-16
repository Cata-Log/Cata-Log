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
from .regions import Germany


class AldiSued(Provider):
    """Provider class for Aldi-Süd current catalog."""

    uid = "aldi-sued-de"
    name = "Aldi-Süd"
    url = "https://www.aldi-sued.de/prospekte"
    region = Germany
    description = "Aldi Süd Katalog"
    first_page_number = 0

    overview_url_format = "https://prospekt.aldi-sued.de/kw{week_number:02}-{relevant_datetime:%y}-op-mp/spreads.json"
    base_url = "https://view.publitas.com"

    @override
    def _get_catalog_data(self) -> None:
        self.catalog_data = self._client.get(
            self.overview_url_format.format(
                week_number=get_calendar_week_number(self._relevant_datetime),
                relevant_datetime=self._relevant_datetime,
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
            - timedelta(days=self._relevant_datetime.weekday() - Day.MONDAY),
            time.min,
            self._relevant_datetime.tzinfo,
        )

    @override
    def _get_valid_until(self) -> datetime:
        return self._get_valid_since() + timedelta(days=7)


class AldiSuedPreview(Preview, AldiSued):
    """Provider class for Aldi-Süd preview catalog for next week."""

    uid = AldiSued.uid + "-preview"
    name = AldiSued.name + "-Vorschau"
    description = AldiSued.description + " für nächste Woche"
    overview_url_format = "https://prospekt.aldi-sued.de/kw{week_number:02}-{relevant_datetime:%y}-op/spreads.json"
    preview_timedelta = timedelta(days=7)


class AldiSuedPrepreview(Preview, AldiSued):
    """Provider class for Aldi-Süd preview catalog for the second-next week."""

    uid = AldiSuedPreview.uid + "-2"
    name = AldiSued.name + "-Vorvorschau"
    description = AldiSued.description + " für übernächste Woche"
    overview_url_format = "https://prospekt.aldi-sued.de/kw{week_number:02}-{relevant_datetime:%y}-vop/spreads.json"
    preview_timedelta = timedelta(days=14)
