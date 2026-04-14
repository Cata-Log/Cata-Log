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

from cata_log.exceptions import CatalogUnavailableWarning, PagesExhausted
from cata_log.utils.page_numbers import PageNumber

from .base import Preview, Provider
from .configuration import Configuration
from .regions import Germany, Italy


class LidlDeutschland(Provider):
    """Provider class for the current german Lidl catalog."""

    name = "lidl"
    description = "Lidl Angebote"
    url = "https://www.lidl.de/c/online-prospekte/s10005610"
    region = Germany
    configuration = (
        Configuration(
            name="region_id",
            helptext="""ID der Lidl Region.
            Öffne lidl.de und wähle deine Filiale.
            Öffne den Web-Inspektor und suche im Webspeicher nach einem Cookie namens 'wh'.
            Der Wert dieses Cookies ist eine Zahl, die Region-ID.
            """,
            default="0",
        ),
    )
    first_page_number = 0

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?region_id={region_id}&client_locale=lidl/{language_code_lower}-{language_code_upper}"
    flyer_index = 0

    @override
    def _get_catalog_data(self) -> None:
        overview_response = self._client.get(
            self.overview_url_template.format(
                **self._config,
                language_code_lower=self.region.language_code.lower(),
                language_code_upper=self.region.language_code.upper(),
            )
        )
        flyer_json_response = self._client.get(
            overview_response.json()["categories"][0]["subcategories"][0]["flyers"][
                self.flyer_index
            ]["flyerJson"]
        )
        self.flyer_json = flyer_json_response.json()

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        try:
            url = self.flyer_json["flyer"]["pages"][int(page_number)]["image"]
        except IndexError as error:
            raise PagesExhausted from error
        response = self._client.get(url)
        return response.content

    @override
    def _get_valid_since(self) -> datetime:
        return datetime.strptime(
            self.flyer_json["flyer"]["offerStartDate"], "%Y-%m-%d"
        ).astimezone(tz=self.region.timezone)

    @override
    def _get_valid_until(self) -> datetime:
        return datetime.strptime(
            self.flyer_json["flyer"]["offerEndDate"], "%Y-%m-%d"
        ).astimezone(tz=self.region.timezone) + timedelta(days=1)


class LidlDeutschlandPreview(Preview, LidlDeutschland):
    """Provider class for Lidl preview catalog for next week."""

    name = "lidl-preview"
    description = LidlDeutschland.description + " nächste Woche"
    flyer_index = 1
    preview_timedelta = timedelta(days=7)

    @override
    def _get_catalog_data(self) -> None:
        try:
            super()._get_catalog_data()
        except IndexError as index_error:
            raise CatalogUnavailableWarning from index_error


class LidlDeutschlandPrepreview(LidlDeutschlandPreview):
    """Provider class for Lidl preview catalog for second-next week."""

    name = "lidl-prepreview"
    description = LidlDeutschland.description + " übernächste Woche"
    flyer_index = 2
    preview_timedelta = timedelta(days=14)


class LidlItalia(LidlDeutschland):
    """Provider class for the current italian Lidl catalog."""

    region = Italy
    name = "lidl"
    description = "Offerte Lidl"

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?region_id={region_id}&client_locale=lidl/it-IT"
