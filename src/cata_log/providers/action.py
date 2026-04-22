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

from .base import Provider
from .regions import Germany


class Action(Provider):
    """Provider class for Action current catalog."""

    uid = "action-de"
    name = "Action"
    url = "https://www.action.com/de-de/prospekt/"
    region = Germany
    description = "Action Katalog"
    first_page_number = 0

    overview_url_format = "https://de.publications.action.com/action-week-{week_number:02}-{year}/spreads.json"
    base_url = "https://de.publications.action.com/"

    @override
    def _get_catalog_data(self) -> None:
        valid_since = self.get_valid_since()
        self.catalog_data = self._client.get(
            self.overview_url_format.format(
                week_number=get_calendar_week_number(valid_since),
                year=valid_since.year,
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
            - timedelta(days=(self._relevant_datetime.weekday() - Day.WEDNESDAY) % 7),
            time.min,
            self._relevant_datetime.tzinfo,
        )

    @override
    def _get_valid_until(self) -> datetime:
        return self._get_valid_since() + timedelta(days=7)
