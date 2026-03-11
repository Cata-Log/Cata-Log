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
import zoneinfo

from cata_log.constants import WeekCountingStartpoints


class Region(abc.ABC):
    local_name: str
    week_counting_startpoint: WeekCountingStartpoints
    timezone: zoneinfo.ZoneInfo
    language_code: str
    is_rtl: bool = False

    @classmethod
    def info(cls) -> dict[str, str]:
        return {
            "timezone": str(cls.timezone),
            "language_code": cls.language_code,
            "local_name": cls.local_name,
        }


class Germany(Region):
    week_counting_startpoint = WeekCountingStartpoints.MONDAY
    timezone = zoneinfo.ZoneInfo("Europe/Berlin")
    language_code = "de"
    local_name = "Deutschland"


class Austria(Germany):
    local_name = "Österreich"
    timezone = zoneinfo.ZoneInfo("Europe/Vienna")
