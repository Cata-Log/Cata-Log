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

from cata_log.exceptions import PagesExhausted
from cata_log.utils.page_numbers import PageNumber

from .base import Provider
from .configuration import Configuration
from .regions import Germany


class KauflandWoche(Provider):
    """Provider class for Kaufland Wochenangebote catalog."""

    name = "kaufland"
    description = "Kaufland Angebote"
    configuration = (
        Configuration(name="region_id", helptext="ID der Kaufland-Region"),
    )
    url = "https://filiale.kaufland.de/prospekte.html"
    region = Germany
    first_page_number = 0

    overview_url_template = "https://endpoints.leaflets.schwarz/v4/overview/?region_id={region_id}&client_locale=kaufland/de-DE"

    @override
    def _get_catalog_data(self) -> None:
        overview_response = self._client.get(
            self.overview_url_template.format(**self._config)
        )
        flyer_json_response = self._client.get(
            overview_response.json()["categories"][0]["subcategories"][-2]["flyers"][0][
                "flyerJson"
            ]
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


class KauflandWochePreview(KauflandWoche):
    """Provider class for Kaufland Wochenangebote preview catalog for next week."""

    name = "kaufland-preview"
    description = KauflandWoche.description + " im nächsten Katalog"

    @override
    def _get_catalog_data(self) -> None:
        overview_response = self._client.get(
            self.overview_url_template.format(**self._config)
        )
        flyer_json_response = self._client.get(
            overview_response.json()["categories"][0]["subcategories"][-2]["flyers"][1][
                "flyerJson"
            ]
        )
        self.flyer_json = flyer_json_response.json()
