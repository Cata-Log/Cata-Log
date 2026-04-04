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

from collections.abc import Sequence
from typing import override

from cata_log.constants import StatusEnum


class ApplicationMisconfiguredError(Exception):
    """An error indicating a bad app configuration."""


class ProviderWarning(Warning):
    """A warning about a provider."""

    provider_status: StatusEnum


class NetworkError(Exception):
    """An error with the network."""


class ProviderBrokenWarning(ProviderWarning):
    """An error indicating that the provider class may be broken."""

    provider_status = StatusEnum.BROKEN


class ProviderRegistrationWarning(ProviderBrokenWarning):
    """An error indicating that the provider class could not be registered."""


class ProviderMisconfiguredWarning(ProviderWarning):
    """An error indicating that the provider is misconfigured."""

    provider_status = StatusEnum.MISCONFIGURED


class ProviderIncompleteConfigWarning(ProviderMisconfiguredWarning):
    """An error indicating that the provider config is incomplete."""

    @override
    def __init__(self, missing_configs: Sequence[str]) -> None:
        self.missing_configs = missing_configs
        super().__init__("Provider configuration is incomplete.")


class ProviderInvalidConfigWarning(ProviderMisconfiguredWarning):
    """An error indicating that a provider config is invalid."""

    @override
    def __init__(self, bad_configs: Sequence[str]) -> None:
        self.bad_configs = bad_configs
        super().__init__("Provider configuration is invalid.")


class ProviderUnknownClassWarning(ProviderMisconfiguredWarning):
    """An error indicating that the provider class-id is unknown."""

    @override
    def __init__(self, class_id: str) -> None:
        self.class_id = class_id
        super().__init__("Provider type is unknown.")


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
