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

from pydantic import Field

from cata_log_hub.utils.page_numbers import PageNumber

from .base import Provider
from .regions import Germany


class EdekaMarkt(Provider):
    """Provider class for Edeka Marktangebote catalog."""

    uid = "edeka-markt-de"
    name = "Edeka-Markt"
    description = "Edeka Markt Angebote"
    url = "https://www.edeka-wochenangebote.de/"
    region = Germany

    class Configuration(Provider.Configuration):
        region: str = Field(
            description="""Name der Region.
                Öffne edeka.de und öffne den Onlinekatalog deines Marktes.
                Öffne den Web-Inspektor und gehe auf den Netzwerk-Tab.
                Lade die Seite neu.
                Suche die bk_1.jpg Datei und ihre URL.
                Diese ist wie folgt aufgebaut: https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/thumbnails/bk_0.jpg
                Die beiden Platzhalter stehen für Region und Marktnamen.
                """,
        )
        edeka_markt: str = Field(
            description="""Name des Edeka Marktes.
                Öffne edeka.de und öffne den Onlinekatalog deines Marktes.
                Öffne den Web-Inspektor und gehe auf den Netzwerk-Tab.
                Lade die Seite neu.
                Suche die bk_1.jpg Datei und ihre URL.
                Diese ist wie folgt aufgebaut: https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/thumbnails/bk_0.jpg
                Die beiden Platzhalter stehen für Region und Marktnamen.
                """
        )

    url_format = "https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/normal/bk_{page_number}.jpg"

    @override
    def _get_catalog_data(self) -> None:
        pass

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        response = self._client.get(
            self.url_format.format(
                region=self._configuration.region,
                edeka_markt=self._configuration.edeka_markt,
                page_number=page_number,
            ),
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
