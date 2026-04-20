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
from typing import Any

from pydantic import AwareDatetime, field_validator


class AwareDatetimesMixin:
    """Mixin for aware datetimes."""

    @field_validator("*", mode="before")
    @classmethod
    def make_datetimes_aware(cls, value: Any) -> Any:  # noqa: ANN401 # no reason to be precise here
        """Add a timezone to naive datetime values.

        Returns:
            The aware datetime.
        """
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.astimezone(UTC)
        return value


class AwareTimestampsMixin(AwareDatetimesMixin):
    """Mixin for api data with aware datetimes and database timestamps."""

    created_at: AwareDatetime
    updated_at: AwareDatetime
