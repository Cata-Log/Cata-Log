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

from .action import Action
from .aldi_nord import (
    AldiNord,
    AldiNordPreview,
)
from .aldi_sued import (
    AldiSued,
    AldiSuedPrepreview,
    AldiSuedPreview,
)
from .base import Provider
from .edeka import EdekaMarkt
from .hofer import Hofer, HoferPreview
from .kaufland import KauflandSonder, KauflandWoche, KauflandWochePreview
from .kik import Kik
from .lidl import (
    LidlDeutschland,
    LidlDeutschlandPrepreview,
    LidlDeutschlandPreview,
    LidlItalia,
)
from .metro import MetroWochenangebote, MetroWochenangebotePreview
from .netto import Netto, NettoPreview
from .norma import Norma
from .penny import Penny, PennyPreview
from .plugins import load_plugins
from .rewe import Rewe, RewePreview
from .rossmann import RossmannAktion, RossmannBeilage

__all__ = [
    "Action",
    "AldiNord",
    "AldiNordPreview",
    "AldiSued",
    "AldiSuedPrepreview",
    "AldiSuedPreview",
    "EdekaMarkt",
    "Hofer",
    "HoferPreview",
    "KauflandSonder",
    "KauflandWoche",
    "KauflandWochePreview",
    "Kik",
    "LidlDeutschland",
    "LidlDeutschlandPrepreview",
    "LidlDeutschlandPreview",
    "LidlItalia",
    "MetroWochenangebote",
    "MetroWochenangebotePreview",
    "Netto",
    "NettoPreview",
    "Norma",
    "Penny",
    "PennyPreview",
    "Provider",
    "Rewe",
    "RewePreview",
    "RossmannAktion",
    "RossmannBeilage",
]

load_plugins()
