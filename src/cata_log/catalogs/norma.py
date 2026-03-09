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

from cata_log import exceptions
from cata_log.utils.dates import get_calendar_week_number

from .base import Base
from .regions import Germany
from .registry import catalog_registry


@catalog_registry.register
class Norma(Base):
    id = "norma"
    description = "Norma Angebote"
    region = Germany

    catalog_url_format = "https://www.norma-online.de/de/angebote/online-prospekt/{year}-{week_number:02}_FG/files/page/{page_number}.jpg"

    @override
    def get_page(self, page_number: int) -> bytes:
        response = httpx.get(
            url=self.catalog_url_format.format(
                year=self._relevant_datetime.year,
                week_number=get_calendar_week_number(
                    self._relevant_datetime, self.region.week_counting_startpoint
                ),
                page_number=page_number,
            ),
            follow_redirects=True,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code == httpx.codes.NOT_FOUND:
                raise exceptions.NotFoundError from error
            raise exceptions.InvalidURLError from error
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
class NormaPreview(Norma):
    id = "norma-preview"
    description = Norma.description + " nächste Woche"

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=7)


@catalog_registry.register
class NormaPreview2(Norma):
    id = "norma-preview2"
    description = Norma.description + " übernächste Woche"

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=14)
