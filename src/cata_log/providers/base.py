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
import logging
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
    """The name of this catalog provider"""
    description: str
    """The user-facing description for this provider"""
    url: str
    """The url of this catalog provider"""
    region: type[Region]
    """The region this catalog is issued in"""
    first_page_number: int = 1
    """The number of the first page in the providers api"""
    configuration: MappingProxyType[str, str] = MappingProxyType({})
    """The configuration parameters with helptexts for this provider"""
    schedule: crontab = crontab(hour=4)
    """The crontab schedule for fetching this provider"""

    @final
    def __init__(self, **kwargs: Any):
        """Constructor for a provider instance.

        Stores all kwargs into a the :attr:`_config` member.
        """
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
        self._logger = logging.getLogger(self.__class__.__name__)

    @final
    def __init_subclass__(cls) -> None:
        """Subclass constructor.
        Adds the subclass to the registry.
        """
        super().__init_subclass__()
        if cls.id() in cls.registry:
            raise AttributeError(f"The ID of {cls} is not unique.")
        cls.registry[cls.id()] = cls

    @final
    def __enter__(self) -> Self:
        """Entrypoint for the context manager."""
        return self

    @final
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        """Exitpoint for the context manager.
        Closes the httpx client.

        Args:
            exc_type: The type of the exception raised in the context.
            exc_value: The exception raised in the context.
            exc_traceback: The traceback of the exception raised in the context.
        """
        self._client.close()

    @final
    def __str__(self) -> str:
        """String representation of this provider."""
        return f"Catalog {self.id}"

    def get_relevant_datetime(self) -> datetime:
        """Get the datetime that defines the catalog offered by this provider.
        The current datetime for current catalogs, a future datetime for preview catalogs.

        Returns:
            The current datetime in the providers regional timezone.
        """
        return datetime.now(tz=self.region.timezone)

    @abc.abstractmethod
    def get_valid_since(self) -> datetime:
        """Get the datetime since which this providers catalog is valid."""

    @abc.abstractmethod
    def get_valid_until(self) -> datetime:
        """Get the datetime until which this providers catalog is valid."""

    @abc.abstractmethod
    def get_page(self, page_number: int) -> bytes:
        """Get one page from the provider.

        Args:
            page_number: The number of the page in the numbering of the provider.

        Returns:
            The downloaded page in bytes.
        """

    @abc.abstractmethod
    def get_catalog_data(self) -> None:
        """Get and store the data for this providers catalog.
        Can be passed if no data beside the pagenumber is required to fetch pages from the provider.
        """

    @final
    def iter_catalog_pages(self) -> Generator[tuple[int, bytes]]:
        """Iterate over pages of this providers catalog.

        Args:
            page_range: An optional range of pagenumbers to fetch. Omit this to fetch all.

        Returns:
            A generator of the pages data as bytes.
        """
        try:
            self._logger.debug("Getting catalog data ...")
            try:
                self.get_catalog_data()
            except httpx.HTTPStatusError as status_error:
                self._logger.exception("Getting catalog data failed!")
                raise ProviderMisconfiguredOrBrokenWarning from status_error
            self._logger.debug("Success getting catalog data.")

            page_number = self.first_page_number
            while True:
                self._logger.debug("Getting page %s ...", page_number)
                try:
                    yield page_number, self.get_page(page_number)
                except PagesExhausted:
                    self._logger.debug("Page %s was the last page.", page_number - 1)
                    break
                except httpx.HTTPStatusError as status_error:
                    if (
                        status_error.response.status_code == httpx.codes.NOT_FOUND
                        and page_number != self.first_page_number
                    ):
                        self._logger.debug(
                            "Page %s appear to be the last page.",
                            page_number - 1,
                            exc_info=True,
                        )
                        break
                    self._logger.exception("Failed getting page %s.", page_number)
                    raise ProviderMisconfiguredOrBrokenWarning from status_error
                page_number += 1
        except httpx.TransportError as transport_error:
            self._logger.exception("Failed getting catalog pages.")
            raise NetworkError from transport_error
        except Exception as error:
            self._logger.exception("Failed getting catalog pages.")
            raise ProviderBrokenWarning from error

    @final
    @classmethod
    def id(cls) -> str:
        """Build a unique identifier for this provider class based on :attr:`name and the local name of :attr:`region`.

        Returns:
            A unique id for this provider class.
        """
        return cls.name + "-" + cls.region.local_name.lower()

    @classmethod
    def info(cls) -> dict[str, str | dict[str, str]]:
        """Get user-relevant info about this provider.

        Returns:
            A dictionary containing class attributes of this provider class.
        """
        return {
            "id": cls.id(),
            "description": cls.description,
            "url": cls.url,
            "configuration": dict(cls.configuration),
            "region": cls.region.info(),
        }
