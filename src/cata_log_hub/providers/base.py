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
from datetime import datetime, timedelta
from types import TracebackType
from typing import Any, ClassVar, Self, final, override

import httpx
from fake_useragent import UserAgent
from pydantic import BaseModel, ValidationError

from cata_log_hub.exceptions import (
    CatalogUnavailableWarning,
    NetworkError,
    PagesExhausted,
    ProviderBrokenWarning,
    ProviderInvalidConfigurationWarning,
    ProviderMisconfiguredOrBrokenWarning,
    ProviderUnknownClassWarning,
    ProviderWarning,
)
from cata_log_hub.settings import get_settings
from cata_log_hub.utils.page_numbers import PageNumber, page_numbering

from .regions import Region


class Provider(abc.ABC):
    """Abstract base class for all catalog providers."""

    _registry: ClassVar[dict[str, type[Provider]]] = {}
    uid: str
    """A unique identifier for this provider class. Must not be changed after definition."""
    name: str
    """The name of this catalog provider."""
    description: str
    """The user-facing description for this provider"""
    url: str
    """The url of this catalog provider"""
    region: type[Region]
    """The region this catalog is issued in"""
    first_page_number: int = 1
    """The number of the first page in the providers api"""
    schedule: str = "0 4 * * *"
    """The crontab schedule for fetching this provider"""
    jitter: int = 3600
    """Jitter for the schedule timing in seconds."""

    class Configuration(BaseModel):
        """The configuration for this provider."""

    @final
    @override
    def __init__(self, configuration: dict[str, str]) -> None:
        """Constructor for a provider instance.

        Attributes:
            _configuration: An instance of the :class:`cata_log_hub.base.Provider.Configuration` loaded from :param:`configuration` .
            _client: HTTPX client instance that throws on every error status and follows redirects.
            _relevant_datetime: The relevant datetime defining the catalog to cache.
        """
        self._configuration = self.validate_configuration(configuration)
        self._relevant_datetime = self.get_relevant_datetime()
        self._client = httpx.Client(
            follow_redirects=True,
            headers={"User-Agent": UserAgent().random},
            event_hooks={
                "response": [
                    lambda r, *_, **__: r.raise_for_status() if r.is_error else None,
                ]
            },
            timeout=get_settings().request_timeout,
        )
        self.get_catalog_data()

    @final
    @override
    def __init_subclass__(cls) -> None:
        """Subclass constructor.
        Initializes a logger and adds the subclass to the registry.
        """
        super().__init_subclass__()
        cls._logger = logging.getLogger(cls.__module__ + "." + cls.__name__)
        if cls.uid in cls._registry:
            cls._logger.error(
                "Provider has a duplicate UID and can't be registered!",
                extra={"uid": cls.uid},
            )
            return
        cls._registry[cls.uid] = cls

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
        Closes :attr:`client`.

        Args:
            exc_type: The type of the exception raised in the context.
            exc_value: The exception raised in the context.
            exc_traceback: The traceback of the exception raised in the context.
        """
        self._cleanup()
        self._client.close()

    def _cleanup(self) -> None:  # noqa: B027 # should do nothing by default
        """Additional cleanup."""

    def get_relevant_datetime(self) -> datetime:
        """Get the datetime that defines the catalog offered by this provider.
        The current datetime for current catalogs, a future datetime for preview catalogs.
        Used to set :attr:`_relevant_datetime`.

        Returns:
            The current datetime in the providers regional timezone.
        """
        return datetime.now(tz=self.region.timezone)

    @abc.abstractmethod
    def _get_valid_since(self) -> datetime:
        """Get the datetime since which this providers catalog is valid."""

    @final
    def get_valid_since(self) -> datetime:
        """_get_valid_since wrapped in error handling.

        Raises:
            :exc:`cata_log_hub.exceptions.ProviderBrokenWarning`: If any exception is raise in getting the valid_since timestamp.
        """
        try:
            result = self._get_valid_since()
        except Exception as error:
            raise ProviderBrokenWarning from error
        if not result.tzinfo:
            return result.replace(tzinfo=self.region.timezone)
        return result

    @abc.abstractmethod
    def _get_valid_until(self) -> datetime:
        """Get the datetime until which this providers catalog is valid."""

    @final
    def get_valid_until(self) -> datetime:
        """_get_valid_until wrapped in error handling.

        Raises:
            :exc:`cata_log_hub.exceptions.ProviderBrokenWarning`: If any exception is raise in getting the valid_until timestamp.
        """
        try:
            result = self._get_valid_until()
        except Exception as error:
            raise ProviderBrokenWarning from error
        if not result.tzinfo:
            return result.replace(tzinfo=self.region.timezone)
        return result

    @abc.abstractmethod
    def _get_page(self, page_number: PageNumber) -> bytes:
        """Get one page from the provider.

        Args:
            page_number: The number of the page in the numbering of the provider.

        Returns:
            The downloaded page in bytes.
        """

    def get_page(self, page_number: PageNumber) -> bytes:
        """_get_page wrapped in error handling.

        Raises:
            :exc:`cata_log_hub.exceptions.PagesExhausted`:
                If page_number is not first_page_number and pages are exhausted or a :exc:`httpx.HTTPStatusError` is raised.
            :exc:`cata_log_hub.exceptions.CatalogUnavailableWarning`:
                If page_number is first_page_number and the catalog is unavailable.
            :exc:`cata_log_hub.exceptions.ProviderMisconfiguredOrBrokenWarning`:
                If page_number is first_page_number and pages are exhausted or a :exc:`httpx.HTTPStatusError` is raised or the catalog is unavailable.
            :exc:`cata_log_hub.exceptions.NetworkError`:
                If a :exc:`httpx.TransportError` is raised.
            :exc:`cata_log_hub.exceptions.ProviderBrokenWarning`:
                If any other exception is raised.
        """
        self._logger.debug("Getting page %s ...", page_number)
        try:
            result = self._get_page(page_number)
        except PagesExhausted as pages_exhausted:
            if page_number == self.first_page_number:
                raise ProviderMisconfiguredOrBrokenWarning from pages_exhausted.__cause__
            raise
        except CatalogUnavailableWarning as catalog_unavailable_error:
            if page_number != self.first_page_number:
                raise ProviderMisconfiguredOrBrokenWarning from catalog_unavailable_error.__cause__
            raise
        except httpx.HTTPStatusError as status_error:
            if status_error.response.is_error and page_number != self.first_page_number:
                self._logger.debug(
                    "Page %s appears to be the last page.",
                    page_number - 1,
                    exc_info=True,
                )
                raise PagesExhausted from status_error
            self._logger.exception("Failed getting page %s.", page_number)
            raise ProviderMisconfiguredOrBrokenWarning from status_error
        except httpx.TransportError as transport_error:
            self._logger.exception("Failed getting catalog pages.")
            raise NetworkError from transport_error
        except Exception as error:
            self._logger.exception("Failed getting catalog pages.")
            raise ProviderBrokenWarning from error
        self._logger.debug("Success getting page %s.", page_number)
        return result

    @abc.abstractmethod
    def _get_catalog_data(self) -> None:
        """Get and store the data for this providers catalog.
        Can be passed if no data beside the pagenumber is required to fetch pages from the provider.
        """

    def get_catalog_data(self) -> None:
        """_get_catalog_data wrapped in error handling.

        Raises:
            :exc:`cata_log_hub.exceptions.CatalogUnavailableWarning`:
                If the catalog is unavailable.
            :exc:`cata_log_hub.exceptions.ProviderMisconfiguredOrBrokenWarning`:
                If a :exc:`httpx.HTTPStatusError` is raised.
            :exc:`cata_log_hub.exceptions.NetworkError`:
                If a :exc:`httpx.TransportError` is raised.
            :exc:`cata_log_hub.exceptions.ProviderBrokenWarning`:
                If any other exception is raised.
        """
        self._logger.debug("Getting catalog data ...")
        try:
            self._get_catalog_data()
        except CatalogUnavailableWarning:
            self._logger.exception("Failed getting catalog data.")
            raise
        except httpx.HTTPStatusError as status_error:
            self._logger.exception("Failed getting catalog data.")
            raise ProviderMisconfiguredOrBrokenWarning from status_error
        except httpx.TransportError as transport_error:
            self._logger.exception("Failed getting catalog data.")
            raise NetworkError from transport_error
        except Exception as error:
            self._logger.exception("Failed getting catalog data.")
            raise ProviderBrokenWarning from error
        self._logger.debug("Success getting catalog data.")

    @final
    def iter_catalog_pages(self) -> Generator[tuple[int, bytes]]:
        """Iterate over pages of this providers catalog.

        Returns:
            A generator of the pages data as bytes.
        """
        for page_number in page_numbering(
            self.first_page_number
        ):  # pragma: no branch # this iterator never finishes
            try:
                yield page_number.normalized, self.get_page(page_number)
            except PagesExhausted:
                self._logger.debug("Page %s was the last page.", page_number - 1)
                break

    @final
    @classmethod
    def get_class(cls, class_uid: str) -> type[Provider]:
        """Get the provider class to a given class-id.

        Args:
            class_uid: The class-id to get the provider for.

        Returns:
            The class to the class-id.

        Raises:
            :exc:`cata_log_hub.exceptions.ProviderUnknownClassWarning`: If there is no class for the given uid.
        """
        provider_class = cls._registry.get(class_uid)
        if not provider_class:
            raise ProviderUnknownClassWarning
        return provider_class

    @final
    @classmethod
    def get_class_uids(cls) -> list[str]:
        """Get all registered class-ids.

        Returns:
            A set of all registered class identifiers.
        """
        return list(cls._registry.keys())

    @final
    @classmethod
    def get_classes(cls) -> list[type[Provider]]:
        """Get all registered classes.

        Returns:
            A set of all registered classes.
        """
        return list(cls._registry.values())

    @final
    @classmethod
    def validate_configuration(
        cls, configuration_dict: dict[str, Any]
    ) -> Configuration:
        """Validate a given configuration and return the validated version.

        Args:
            configuration_dict: The configuration dictionary to validate.

        Returns:
            The validated configuration.

        Raises:
            :exc:`cata_log_hub.exceptions.ProviderInvalidConfigurationWarning`:
                If the given configuration is incomplete or otherwise invalid.
        """
        try:
            validated_configuration = cls.Configuration.model_validate(
                configuration_dict
            )
        except ValidationError as validation_error:
            raise ProviderInvalidConfigurationWarning from validation_error
        return validated_configuration


# mypy: disable_error_code=misc
# mypy: disable_error_code=no-any-return
class Preview(abc.ABC):
    """Preview mixin for a provider class."""

    @abc.abstractmethod
    def _get_preview_timedelta(self) -> timedelta:
        """Get the dynamic timedelta between the relevant datetime and the relevant datetime of the preview.

        Returns:
            The preview timedelta.
        """

    @final
    def get_preview_timedelta(self) -> timedelta:
        """Get the preview timedelta with error handling.

        Returns:
            The preview timedelta.

        Raises:
            :exc:`cata_log_hub.exceptions.ProviderBrokenWarning`: If any exception is raised.
        """
        try:
            preview_timedelta = self._get_preview_timedelta()
        except Exception as error:
            raise ProviderBrokenWarning from error
        return preview_timedelta

    @override
    def get_relevant_datetime(self) -> datetime:
        return super().get_relevant_datetime() + self.get_preview_timedelta()

    @override
    def get_catalog_data(self) -> None:
        try:
            super().get_catalog_data()
        except ProviderWarning as provider_warning:
            if isinstance(provider_warning.__cause__, httpx.HTTPStatusError):
                raise CatalogUnavailableWarning from provider_warning.__cause__
            raise

    @override
    def get_page(self, page_number: PageNumber) -> bytes:
        try:
            return super().get_page(page_number)
        except ProviderWarning as provider_warning:
            if (
                isinstance(provider_warning.__cause__, httpx.HTTPStatusError)
                and page_number == self.first_page_number
            ):
                raise CatalogUnavailableWarning from provider_warning.__cause__
            raise
