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

from cata_log import exceptions

from .base import Base
from .regions import Germany
from .registry import catalog_registry


@catalog_registry.register
class EdekaBasis(Base):
    id = "edeka-basis"
    description = "Edeka Basis Angebote"
    configuration = MappingProxyType(
        {
            "region": "Name der Edeka Region",
        }
    )
    region = Germany

    url_format = "https://blaetterkatalog.edeka.de/{region}/EDEKA_CENTER_GRUND_SORTIMENT_{edeka_region}/blaetterkatalog/normal/bk_{page_number}.jpg"

    @override
    def __init__(self, region: str, edeka_region: str, **kwargs: Any) -> None:
        super().__init__(**kwargs, region=region, edeka_region=edeka_region)

    @override
    def get_page(self, page_number: int) -> bytes:
        response = httpx.get(
            self.url_format.format(**self._config, page_number=page_number),
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
class EdekaMarkt(EdekaBasis):
    id = "edeka-markt"
    description = "Edeka Markt Angebote"
    region = Germany
    configuration = MappingProxyType(
        {
            "region": "Name der Edeka Region",
            "edeka_markt": "Name des Edeka Marktes",
        }
    )
    url_format = "https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/normal/bk_{page_number}.jpg"

    @override
    def __init__(self, region: str, edeka_markt: str, **kwargs: Any) -> None:
        super().__init__(**kwargs, region=region, edeka_markt=edeka_markt)
