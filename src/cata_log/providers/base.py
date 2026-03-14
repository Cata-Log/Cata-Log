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
from collections.abc import Generator
from datetime import datetime
from types import MappingProxyType, TracebackType
from typing import Any, ClassVar, Self, final

import httpx
from celery.schedules import crontab

from cata_log.exceptions import (
    NetworkError,
    PagesExhausted,
    ProviderBrokenWarning,
    ProviderMisconfiguredOrBrokenWarning,
)
from cata_log.utils.shortcuts import get_config

from .regions import Region


class Provider(abc.ABC):
    """Abstract base class for all catalog providers."""

    registry: ClassVar[dict[str, type[Provider]]] = {}
    name: str
    description: str
    url: str
    region: type[Region]
    first_page_number: int = 1
    configuration: MappingProxyType[str, str] = MappingProxyType({})
    schedule: crontab = crontab(hour=4)

    @final
    def __init__(self, **kwargs: Any):
        if any(config_key not in kwargs for config_key in self.configuration):
            raise TypeError("Configuration keyword-argument missing.")
        self._config = kwargs
        self._relevant_datetime = self.get_relevant_datetime()
        self._client = httpx.Client(
            follow_redirects=True,
            headers={"User-Agent": get_config("fake_user_agent")},
            event_hooks={
                "response": [
                    lambda r, *_, **__: r.raise_for_status(),
                ]
            },
        )

    @final
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.id() in cls.registry:
            raise AttributeError(f"The ID of {cls} is not unique.")
        cls.registry[cls.id()] = cls

    @final
    def __enter__(self) -> Self:
        return self

    @final
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        self._client.close()

    @final
    def __str__(self) -> str:
        return f"Catalog {self.id}"

    def get_relevant_datetime(self) -> datetime:
        return datetime.now(tz=self.region.timezone)

    @abc.abstractmethod
    def get_valid_since(self) -> datetime:
        pass

    @abc.abstractmethod
    def get_valid_until(self) -> datetime:
        pass

    @abc.abstractmethod
    def get_page(self, page_number: int) -> bytes:
        pass

    @abc.abstractmethod
    def get_catalog_data(self) -> None:
        pass

    @final
    def iter_catalog_pages(self) -> Generator[tuple[int, bytes]]:
        try:
            try:
                self.get_catalog_data()
            except httpx.HTTPStatusError as status_error:
                raise ProviderMisconfiguredOrBrokenWarning from status_error

            page_number = self.first_page_number
            while True:
                try:
                    yield page_number, self.get_page(page_number)
                except PagesExhausted:
                    break
                except httpx.HTTPStatusError as status_error:
                    if (
                        status_error.response.status_code == httpx.codes.NOT_FOUND
                        and page_number != self.first_page_number
                    ):
                        break
                    raise ProviderMisconfiguredOrBrokenWarning from status_error
                page_number += 1
        except httpx.TransportError as transport_error:
            raise NetworkError from transport_error
        except Exception as error:
            raise ProviderBrokenWarning from error

    @final
    @classmethod
    def id(cls) -> str:
        return cls.name + "-" + cls.region.local_name.lower()

    @final
    @classmethod
    def info(cls) -> dict[str, str | dict[str, str]]:
        return {
            "id": cls.id(),
            "description": cls.description,
            "url": cls.url,
            "configuration": dict(cls.configuration),
            "region": cls.region.info(),
        }
