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
from typing import Any, override

import httpx

from cata_log.exceptions import NotFoundError
from cata_log.utils import page_numbers
from cata_log.utils.dates import get_calendar_week_number

from .base import BaseProvider
from .regions import Germany
from .registry import catalog_registry


@catalog_registry.register
class AldiSued(BaseProvider):
    name = "aldi-sued"
    region = Germany
    description = "Aldi Süd Katalog"
    overview_url_format = (
        "https://prospekt.aldi-sued.de/kw{week_number:02}-{year}-op-mp/spreads.json"
    )
    url = "https://view.publitas.com"

    @override
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @override
    def get_catalog_data(self) -> None:
        self.catalog_data = httpx.get(
            self.overview_url_format.format(
                week_number=get_calendar_week_number(self._relevant_datetime),
                year=self._relevant_datetime.year % 100,
            )
        ).json()

    @override
    def get_page(self, page_number: int) -> bytes:
        try:
            image_url = self.catalog_data[
                page_numbers.page_number_2_double_page_number(page_number)
            ]["pages"][page_numbers.page_number_2_double_page_index(page_number)][
                "images"
            ]["at800"]
        except IndexError as error:
            raise NotFoundError from error
        response = httpx.get(self.url + image_url)
        return response.content

    @override
    def get_valid_since(self) -> datetime:
        return datetime.combine(
            self._relevant_datetime
            - timedelta(days=self._relevant_datetime.weekday() - Day.MONDAY),
            time.min,
            self._relevant_datetime.tzinfo,
        )

    @override
    def get_valid_until(self) -> datetime:
        return self.get_valid_since() + timedelta(days=7)


@catalog_registry.register
class AldiSuedPreview(AldiSued):
    name = "aldi-sued-preview"
    description = AldiSued.description + " für nächste Woche"
    overview_url_format = (
        "https://prospekt.aldi-sued.de/kw{week_number:02}-{year}-op/spreads.json"
    )

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=7)


@catalog_registry.register
class AldiSuedPreview2(AldiSued):
    name = "aldi-sued-preview2"
    description = AldiSued.description + " für übernächste Woche"
    overview_url_format = (
        "https://prospekt.aldi-sued.de/kw{week_number:02}-{year}-vop/spreads.json"
    )

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=14)
