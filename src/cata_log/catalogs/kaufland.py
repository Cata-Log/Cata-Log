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

import calendar
from datetime import datetime, time, timedelta
from types import MappingProxyType
from typing import Any, override

import httpx

from cata_log.utils.dates import get_week_limit_dates

from .base import Base
from .regions import Germany
from .registry import catalog_registry


@catalog_registry.register
class Kaufland(Base):
    id = "kaufland"
    description = "Kaufland Angebote"
    configuration = MappingProxyType(
        {
            "filial_id": "ID der Filiale",
            "region_id": "ID der Region",
            "region_code": "Code der Region",
        }
    )
    region = Germany

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?region_id={region_id}&client_locale=kaufland/de-DE"
    flyer_url_template = "https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=aktionsprospekt-{week_start_date}-{week_end_date}-21f2e9&region_id={region_id}&region_code={region_code}"

    @override
    def __init__(
        self, filial_id: str, region_id: str, region_code: str, **kwargs: Any
    ) -> None:
        super().__init__(
            **kwargs,
            filial_id=filial_id,
            region_id=region_id,
            region_code=region_code,
        )

    @override
    def get_page(self, page_number: int) -> bytes:
        week_start_date, week_end_date = get_week_limit_dates(self._relevant_datetime)
        week_end_date -= timedelta(days=1)
        response = httpx.get(
            self.overview_url_template.format(
                week_start_date=week_start_date.strftime("%d-%m-%Y"),
                week_end_date=week_end_date.strftime("%d-%m-%Y"),
                region_id=self._config["region_id"],
                region_code=self._config["region_code"],
            )
        )
        return response.json()

    @override
    def get_valid_since(self) -> datetime:
        return datetime.combine(
            self._relevant_datetime
            - timedelta(days=self._relevant_datetime.weekday() - calendar.Day.MONDAY),
            time.min,
            self._relevant_datetime.tzinfo,
        )

    @override
    def get_valid_until(self) -> datetime:
        return self.get_valid_since() + timedelta(days=7)
