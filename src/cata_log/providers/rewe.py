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
from urllib.parse import urljoin

from pydantic import Field

from cata_log.exceptions import PagesExhausted
from cata_log.utils import dates, page_numbers

from .base import Preview, Provider
from .regions import Germany


class Rewe(Provider):
    """Provider class for Rewe catalog."""

    uid = "rewe-de"
    name = "Rewe"
    description = "Rewe Katalog"
    url = "https://www.rewe.de/angebote/"
    region = Germany

    class Configuration(Provider.Configuration):
        markt_id: str = Field(
            description="""ID des Rewe Markts.
                Öffne rewe.de und wähle deine Filiale.
                Öffne den Web-Inspektor und suche im Webspeicher nach einem Cookie namens 'wksMarketsCookie'.
                Der Cookie ist URL-encoded, normalerweise gibt es eine Option in dekodiert anzuzeigen.
                Im Cookie ist ein Eintrag '"wwIdent":'. Die folgende Zahl (ohne ") ist die Markt-ID.
                """
        )

    first_page_number = 0

    overview_url_format = "https://view.publitas.com/rewe-markt/rewe_{relevant_datetime:%Y}_wk{week_number:02}_{markt_id}/spreads.json"
    base_url = "https://view.publitas.com"

    @override
    def _get_catalog_data(self) -> None:
        self.catalog_data = self._client.get(
            self.overview_url_format.format(
                markt_id=self._configuration.markt_id,
                week_number=dates.get_calendar_week_number(self._relevant_datetime),
                relevant_datetime=self._relevant_datetime,
            )
        ).json()

    @override
    def _get_page(self, page_number: page_numbers.PageNumber) -> bytes:
        double_page_number = page_number.as_double_page_number()
        try:
            image_url = self.catalog_data[double_page_number.number]["pages"][
                double_page_number.side
            ]["images"]["at2400"]
        except IndexError as error:
            raise PagesExhausted from error
        response = self._client.get(urljoin(self.base_url, image_url))
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


class RewePreview(Preview, Rewe):
    """Provider class for Rewe preview catalog."""

    uid = Rewe.uid + "-preview"
    name = Rewe.name + "-Vorschau"
    description = Rewe.description + " nächste Woche"
    schedule = "30 4 * * 6,0"

    @override
    def _get_preview_timedelta(self) -> timedelta:
        return timedelta(days=7)
