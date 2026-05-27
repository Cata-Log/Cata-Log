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

from datetime import datetime, timedelta
from typing import override

from pydantic import Field

from cata_log.exceptions import CatalogUnavailableWarning, PagesExhausted
from cata_log.utils.page_numbers import PageNumber

from .base import Preview, Provider
from .regions import Germany


class KauflandWoche(Provider):
    """Provider class for Kaufland Wochenangebote catalog."""

    uid = "kaufland-de"
    name = "Kaufland"
    description = "Kaufland Angebote"

    class Configuration(Provider.Configuration):
        filial_id: str = Field(
            default="0",
            description="""ID der Kaufland-Filiale.
            Öffne filiale.kaufland.de und wähle deine Filiale aus.
            Öffne den Web-Inspektor und suche im Webspeicher nach einem Cookie namens 'x-aem-variant.
            Der Wert des Cookies beginnt mit DE.
            Die Zahl danach ist die Filial-ID.
            """,
        )

    url = "https://filiale.kaufland.de/prospekte.html"
    region = Germany
    first_page_number = 0

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?region_id={filial_id}&client_locale=kaufland/{language_code_lower}-{language_code_upper}"
    subcategory_name = "KDZ1"
    flyer_index = 0

    @override
    def _get_catalog_data(self) -> None:
        overview_response = self._client.get(
            self.overview_url_template.format(
                filial_id=self._configuration.filial_id,
                language_code_lower=self.region.language_code.lower(),
                language_code_upper=self.region.language_code.upper(),
            )
        )
        try:
            overview_subcategory = next(
                (
                    subcategory
                    for subcategory in overview_response.json()["categories"][0][
                        "subcategories"
                    ]
                    if self.subcategory_name in subcategory["name"]
                ),
                None,
            )
            if overview_subcategory is None:
                raise CatalogUnavailableWarning
            flyer_json_url = overview_subcategory["flyers"][self.flyer_index][
                "flyerJson"
            ]
        except IndexError as index_error:
            raise CatalogUnavailableWarning from index_error
        self.flyer_json = self._client.get(flyer_json_url).json()

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        try:
            url = self.flyer_json["flyer"]["pages"][int(page_number)]["zoom"]
        except IndexError as error:
            raise PagesExhausted from error
        return self._client.get(url).content

    @override
    def _get_valid_since(self) -> datetime:
        return datetime.strptime(
            self.flyer_json["flyer"]["offerStartDate"], "%Y-%m-%d"
        ).replace(tzinfo=self.region.timezone)

    @override
    def _get_valid_until(self) -> datetime:
        return datetime.strptime(
            self.flyer_json["flyer"]["offerEndDate"], "%Y-%m-%d"
        ).replace(tzinfo=self.region.timezone) + timedelta(days=1)


class KauflandWochePreview(Preview, KauflandWoche):
    """Provider class for Kaufland Wochenangebote preview catalog for next week."""

    uid = KauflandWoche.uid + "-preview"
    name = KauflandWoche.name + "-Vorschau"
    description = KauflandWoche.description + " im nächsten Katalog"
    preview_timedelta = timedelta(days=7)

    flyer_index = 1


class KauflandSonder(KauflandWoche):
    """Provider class for Kaufland Sonderangebote catalog."""

    uid = "kaufland-sonder-de"
    name = "Kaufland Sonderprospekt"
    description = "Kaufland Sonderangebote"

    flyer_index = 0
    subcategory_name = "KDZ2"
