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

import tempfile
from calendar import Day
from datetime import datetime, time, timedelta
from io import BytesIO
from typing import override

import pypdfium2
from pydantic import Field

from cata_log_hub.exceptions import PagesExhausted
from cata_log_hub.utils.page_numbers import PageNumber

from .base import Preview, Provider
from .regions import Germany


class Penny(Provider):
    """Provider class for Kaufland Wochenangebote catalog."""

    uid = "penny-de"
    name = "Penny"
    description = "Penny Katalog"
    schedule = "0 3 * * *"

    class Configuration(Provider.Configuration):
        markt_id: str = Field(
            description="""ID des Penny-Markts.
            Öffne penny.de und wähle deinen Markt aus.
            Öffne den Web-Inspektor und öffne den Netzwerktab.
            Öffne einen Onlinekatalog für deinen Markt.
            Es wird eine Datei market_... mit dem Typ json geladen.
            Die Zahl am Ende des Names dieser Datei ist die Markt-ID.
            """,
        )

    url = "https://www.penny.de/angebote#handout"
    region = Germany
    first_page_number = 0

    pdf_url_template = "https://penny-publish.blaetterkatalog.de/frontend/catalogs/{catalog_id}/2/pdf/complete.pdf"
    market_url_template = "https://www.penny.de/.rest/market/markets/market_{markt_id}"
    market_catalog_url_key = "flippingBookURL"

    @override
    def _get_catalog_data(self) -> None:
        market_response = self._client.get(
            self.market_url_template.format(
                markt_id=self._configuration.markt_id,
            )
        )
        catalog_id = market_response.json()[self.market_catalog_url_key].rsplit(
            "=", maxsplit=1
        )[1]
        pdf_catalog_response = self._client.get(
            self.pdf_url_template.format(catalog_id=catalog_id)
        )
        self.temp_pdf_catalog_file = tempfile.NamedTemporaryFile(  # noqa: SIM115 # needs to stay open until the class exits
            suffix="pdf"
        )
        self.temp_pdf_catalog_file.write(pdf_catalog_response.content)
        self.pdf_catalog = pypdfium2.PdfDocument(  # needs manual closing
            self.temp_pdf_catalog_file.name
        )

    @override
    def _get_page(self, page_number: PageNumber) -> bytes:
        try:
            pdf_catalog_page = self.pdf_catalog.get_page(int(page_number))
        except pypdfium2.PdfiumError as error:
            raise PagesExhausted from error
        image_data_io = BytesIO()
        with pdf_catalog_page.render(scale=2).to_pil() as image:
            image.save(image_data_io, format="WEBP")
        image_data_io.seek(0)
        return image_data_io.read()

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

    @override
    def _cleanup(self) -> None:
        if hasattr(self, "pdf_catalog"):
            self.pdf_catalog.close()
        if hasattr(self, "temp_pdf_catalog_file"):
            self.temp_pdf_catalog_file.close()


class PennyPreview(Preview, Penny):
    """Provider class for Kaufland Wochenangebote preview catalog for next week."""

    uid = Penny.uid + "-preview"
    name = Penny.name + "-Vorschau"
    description = Penny.description + " im nächsten Katalog"

    @override
    def _get_preview_timedelta(self) -> timedelta:
        return timedelta(days=7)

    market_catalog_url_key = "nextWeekFlippingBookURL"
