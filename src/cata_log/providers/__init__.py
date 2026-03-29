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

from .aldi import AldiSued, AldiSuedPreview, AldiSuedPreview2
from .base import Provider
from .edeka import EdekaBasissortiment, EdekaMarkt
from .hofer import Hofer, HoferPreview
from .kaufland import KauflandWoche, KauflandWochePreview
from .lidl import Lidl, LidlPreview, LidlPreview2
from .netto import Netto, NettoPreview
from .norma import Norma
from .rewe import Rewe
from .rossmann import RossmannAngebote

__all__ = [
    "AldiSued",
    "AldiSuedPreview",
    "AldiSuedPreview2",
    "EdekaBasissortiment",
    "EdekaMarkt",
    "Hofer",
    "HoferPreview",
    "KauflandWoche",
    "KauflandWochePreview",
    "Lidl",
    "LidlPreview",
    "LidlPreview2",
    "Netto",
    "NettoPreview",
    "Norma",
    "Provider",
    "Rewe",
    "RossmannAngebote",
]
