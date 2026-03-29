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

from cata_log.constants import StatusEnum


class ProviderWarning(Warning):
    """A warning about a provider."""

    provider_status: StatusEnum


class NetworkError(Exception):
    """An error with the network."""


class ProviderBrokenWarning(ProviderWarning):
    """An error indicating that the provider class may be broken."""

    provider_status = StatusEnum.BROKEN


class ProviderMisconfiguredWarning(ProviderWarning):
    """An error indicating that the provider is misconfigured."""

    provider_status = StatusEnum.MISCONFIGURED


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
