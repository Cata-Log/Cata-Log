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

from cata_log.utils.page_numbers import PageNumber

from .base import Provider
from .configuration import Configuration
from .regions import Germany


class EdekaMarkt(Provider):
    """Provider class for Edeka Marktangebote catalog."""

    name = "Edeka-Markt"
    description = "Edeka Markt Angebote"
    url = "https://www.edeka-wochenangebote.de/"
    configuration = (
        Configuration(
            name="region",
            helptext="""Name der Region.
            Öffne edeka.de und öffne den Onlinekatalog deines Marktes.
            Öffne den Web-Inspektor und gehe auf den Netzwerk-Tab.
            Lade die Seite neu.
            Suche die bk_1.jpg Datei und ihre URL.
            Diese ist wie folgt aufgebaut: https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/thumbnails/bk_0.jpg
            Die beiden Platzhalter stehen für Region und Marktnamen.
            """,
        ),
        Configuration(
            name="edeka_markt",
            helptext="""Name des Edeka Marktes.
            Öffne edeka.de und öffne den Onlinekatalog deines Marktes.
            Öffne den Web-Inspektor und gehe auf den Netzwerk-Tab.
            Lade die Seite neu.
            Suche die bk_1.jpg Datei und ihre URL.
            Diese ist wie folgt aufgebaut: https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/thumbnails/bk_0.jpg
            Die beiden Platzhalter stehen für Region und Marktnamen.
            """,
        ),
    )
    region = Germany

    url_format = "https://blaetterkatalog.edeka.de/{region}/{edeka_markt}/blaetterkatalog/normal/bk_{page_number}.jpg"

    @override
    def _get_catalog_data(self) -> None:
        pass

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        response = self._client.get(
            self.url_format.format(**self._configuration, page_number=page_number),
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
