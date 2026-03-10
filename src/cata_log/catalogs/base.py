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

import abc
from collections.abc import Generator, Sequence
from datetime import datetime
from types import MappingProxyType
from typing import Any

from celery.schedules import crontab

from cata_log.exceptions import NotFoundError

from .regions import Region


class Base(abc.ABC):
    """Abstract base class for all catalog providers."""

    id: str
    region: type[Region]
    first_page_number: int = 1
    description: str
    configuration: MappingProxyType[str, str] = MappingProxyType({})
    schedule: crontab = crontab(hour=4)

    def __init__(self, **kwargs: Any):
        self._config = kwargs
        self._relevant_datetime = self.get_relevant_datetime()

    def get_relevant_datetime(self) -> datetime:
        return datetime.now(tz=self.region.timezone)

    @abc.abstractmethod
    def get_valid_since(self) -> datetime:
        pass

    @abc.abstractmethod
    def get_valid_until(cls) -> datetime:
        pass

    @abc.abstractmethod
    def get_page(self, page_number: int) -> bytes:
        pass

    def get_catalog_data(self) -> None:
        pass

    def iter_catalog_pages(
        self, page_range: Sequence[int] | None = None
    ) -> Generator[tuple[int, bytes]]:
        self.get_catalog_data()
        if page_range:
            for page_number in page_range:
                yield page_number, self.get_page(page_number)
        else:
            page_number = self.first_page_number
            while True:
                try:
                    yield page_number, self.get_page(page_number)
                except NotFoundError:
                    break
                page_number += 1

    @classmethod
    def get_storage_path(cls, datetime: datetime, page_number: int):
        return f"{cls.id}_{datetime}_{page_number}"

    @classmethod
    def info(cls) -> dict[str, str | dict[str, str]]:
        return {
            "id": cls.id,
            "description": cls.description,
            "configuration": dict(cls.configuration),
            "region": cls.region.info(),
        }
