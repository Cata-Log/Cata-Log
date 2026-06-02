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

from cata_log_hub.exceptions import CatalogUnavailableWarning, PagesExhausted
from cata_log_hub.utils.page_numbers import PageNumber

from .base import Preview, Provider
from .regions import Germany, Italy


class LidlDeutschland(Provider):
    """Provider class for the current german Lidl catalog."""

    uid = "lidl-de"
    name = "Lidl"
    description = "Lidl Angebote"
    url = "https://www.lidl.de/c/online-prospekte/s10005610"
    region = Germany
    first_page_number = 0

    class Configuration(Provider.Configuration):
        region_id: str = Field(
            default="0",
            description="""ID der Lidl Region.
                Öffne lidl.de und wähle deine Filiale.
                Öffne den Web-Inspektor und suche im Webspeicher nach einem Cookie namens 'wh'.
                Der Wert dieses Cookies ist eine Zahl, die Region-ID.
                """,
        )

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?region_id={region_id}&client_locale=lidl/{language_code_lower}-{language_code_upper}"

    subcategory_name = "Aktionsprospekte"
    category_name = "Filial"
    flyer_index = 0

    @override
    def _get_catalog_data(self) -> None:
        overview_response = self._client.get(
            self.overview_url_template.format(
                region_id=self._configuration.region_id,
                language_code_lower=self.region.language_code.lower(),
                language_code_upper=self.region.language_code.upper(),
            )
        )
        overview_category = next(
            (
                category
                for category in overview_response.json()["categories"]
                if self.category_name in category["name"]
            ),
            None,
        )
        if overview_category is None:
            raise CatalogUnavailableWarning
        overview_subcategory = next(
            (
                subcategory
                for subcategory in overview_category["subcategories"]
                if self.subcategory_name in subcategory["name"]
            ),
            None,
        )
        if overview_subcategory is None:
            raise CatalogUnavailableWarning
        try:
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


class LidlDeutschlandPreview(Preview, LidlDeutschland):
    """Provider class for Lidl preview catalog for next week."""

    uid = LidlDeutschland.uid + "-preview"
    name = LidlDeutschland.name + "-Vorschau"
    description = LidlDeutschland.description + " nächste Woche"
    flyer_index = 1

    @override
    def _get_preview_timedelta(self) -> timedelta:
        return timedelta(days=7)


class LidlDeutschlandPrepreview(LidlDeutschlandPreview):
    """Provider class for Lidl preview catalog for second-next week."""

    uid = LidlDeutschlandPreview.uid + "-2"
    name = LidlDeutschland.name + "-Vorvorschau"
    description = LidlDeutschland.description + " übernächste Woche"
    flyer_index = 2

    @override
    def _get_preview_timedelta(self) -> timedelta:
        return timedelta(days=14)


class LidlItalia(LidlDeutschland):
    """Provider class for the current italian Lidl catalog."""

    uid = "lidl-it"
    region = Italy
    description = "Offerte Lidl"
