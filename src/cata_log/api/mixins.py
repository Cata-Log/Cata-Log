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

from datetime import UTC, datetime

from pydantic import field_validator


class TimestampMixin:
    """Mixin for api data with database timestamps."""

    created_at: datetime
    updated_at: datetime

    @field_validator("created_at")
    @classmethod
    def attach_created_at_timezone(cls, value: datetime) -> datetime:
        """Add UTC timezone to created_at field.

        Args:
            value: The datetime to make aware.

        Returns:
            The aware datetime.
        """
        if value.tzinfo is None:
            return value.astimezone(UTC)
        return value

    @field_validator("updated_at")
    @classmethod
    def attach_updated_at_timezone(cls, value: datetime) -> datetime:
        """Add UTC timezone to a naive updated_at field.

        Args:
            value: The datetime to make aware.

        Returns:
            The aware datetime.
        """
        if value.tzinfo is None:
            return value.astimezone(UTC)
        return value
