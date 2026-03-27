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


class NetworkError(Exception):
    """An error with the network."""


class ProviderBrokenWarning(Warning):
    """An error indicating that the provider class may be broken."""


class ProviderMisconfiguredWarning(Warning):
    """An error indicating that the provider is misconfigured."""


class ProviderMisconfiguredOrBrokenWarning(Warning):
    """An error indicating that the provider class may be broken or misconfigured."""


class PagesExhausted(Exception):  # noqa: N818  # not actually an error
    """The pages of a catalog were exhausted."""


class CatalogNotAvailableError(Exception):
    """The catalog is currently not available.
    This does not mean that the provider is permanently broken.
    """
