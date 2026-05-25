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

from typing import Any, override

from cata_log.constants import StatusEnum


class HealthCheckFailedError(Exception):
    """An error indicating a failed healthcheck."""

    @override
    def __init__(self, *args: object) -> None:
        super().__init__("Healthcheck failed: ", *args)


class ProviderWarning(Warning):
    """A warning about a provider."""

    provider_status: StatusEnum

    @override
    def __init__(self, *args: Any) -> None:
        super().__init__(f"Provider is {self.provider_status.value}.", *args)


class NetworkError(Exception):
    """An error with the network."""


class ProviderBrokenWarning(ProviderWarning):
    """An error indicating that the provider class may be broken."""

    provider_status = StatusEnum.BROKEN


class ProviderMisconfiguredWarning(ProviderWarning):
    """An error indicating that the provider is misconfigured."""

    provider_status = StatusEnum.MISCONFIGURED


class ProviderInvalidConfigurationWarning(ProviderMisconfiguredWarning):
    """An error indicating that a provider configuration is invalid."""

    @override
    def __init__(self, *args: Any) -> None:
        super().__init__("Provider configuration is invalid.", *args)


class ProviderUnknownClassWarning(ProviderMisconfiguredWarning):
    """An error indicating that the provider class-id is unknown."""

    @override
    def __init__(self, *args: Any) -> None:
        super().__init__("Provider class is unknown.", *args)


class ProviderMisconfiguredOrBrokenWarning(ProviderWarning):
    """An error indicating that the provider class may be broken or misconfigured."""

    provider_status = StatusEnum.MISCONFIGURED_OR_BROKEN


class CatalogUnavailableWarning(ProviderWarning):
    """The catalog is currently not available.
    This does not mean that the provider is permanently broken.
    """

    provider_status = StatusEnum.UNAVAILABLE


class PagesExhausted(Exception):  # noqa: N818  # not actually an error
    """The pages of a catalog were exhausted."""
