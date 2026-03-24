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
from typing import override

from cata_log.utils.page_numbers import PageNumber

from .base import Provider
from .regions import Germany


class EdekaBasissortiment(Provider):
    """Provider class for Edeka Basissortiment catalog."""

    name = "edeka-basissortiment"
    description = "Edeka Basis Angebote"
    url = "https://www.edeka-wochenangebote.de/"
    configuration = MappingProxyType(
        {
            "region": "Name der Region",
            "edeka_region": "Name der Edeka Region",
        }
    )
    region = Germany

    url_format = "https://blaetterkatalog.edeka.de/{region}/EDEKA_CENTER_GRUND_SORTIMENT_{edeka_region}/blaetterkatalog/normal/bk_{page_number}.jpg"

    @override
    def _get_catalog_data(self) -> None:
        pass

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        response = self._client.get(
            self.url_format.format(**self._config, page_number=page_number),
        )
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


class EdekaMarkt(EdekaBasissortiment):
    """Provider class for Edeka Marktangebote catalog."""

    name = "edeka-markt"
    description = "Edeka Markt Angebote"
    configuration = MappingProxyType(
        {
            "region": "Name der Edeka Region",
            "edeka_markt": "Name des Edeka Marktes",
        }
    )
    url_format = "https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/normal/bk_{page_number}.jpg"
