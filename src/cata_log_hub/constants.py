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

import calendar
import enum


class StatusEnum(enum.StrEnum):
    """Enum of states for providers."""

    MISCONFIGURED = "misconfigured"
    BROKEN = "broken"
    MISCONFIGURED_OR_BROKEN = "misconfigured-or-broken"
    UNAVAILABLE = "unavailable"
    HEALTHY = "healthy"


class CatalogSchedules(enum.Enum):
    """Enum of all catalog schedule types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class WeekCountingStartpoints(enum.Enum):
    """Enum of all common startpoints for counting a week from."""

    SUNDAY = calendar.Day.SUNDAY
    MONDAY = calendar.Day.MONDAY

    @property
    def week_number_format(self) -> str:
        """The datetime formatter for the enum value.

        Returns:
            The datetime formatter string.
        """
        return "%U" if self.value == calendar.Day.SUNDAY.value else "%W"
