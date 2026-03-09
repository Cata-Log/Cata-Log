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
from types import MappingProxyType
from typing import Any, override

import httpx

from .base import Base
from .regions import Germany
from .registry import catalog_registry


@catalog_registry.register
class Lidl(Base):
    id = "lidl"
    description = "Lidl Angebote"
    region = Germany
    config_explanation = MappingProxyType(
        {
            "region_id": "ID der Lidl Region",
        }
    )

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?client_locale=lidl/de-DE&region_id={region_id}"
    flyer_json_url_template = "https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=aktionsprospekt-{week_start_date}-{week_end_date}-21f2e9&region_id={region_id}"

    @override
    def __init__(self, region_id: str, **kwargs: Any) -> None:
        super().__init__(
            **kwargs,
            region_id=region_id,
        )

    @override
    def get_page(self, page_number: int) -> bytes:
        response = httpx.get(
            self.flyer_json_url_template.format(
                week_start_date=self.get_valid_since().strftime("%d-%m-%Y"),
                week_end_date=(self.get_valid_until() - timedelta(days=1)).strftime(
                    "%d-%m-%Y"
                ),
                **self._config,
            )
        )
        return response.json()

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
class LidlPreview(Lidl):
    id = "lidl-preview"
    description = Lidl.description + " nächste Woche"

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=7)


@catalog_registry.register
class LidlPreview2(Lidl):
    id = "lidl-preview2"
    description = Lidl.description + " übernächste Woche"

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + timedelta(days=14)
