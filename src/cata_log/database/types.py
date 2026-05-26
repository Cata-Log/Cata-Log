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
from pathlib import Path
from typing import override

from sqlalchemy import (
    Dialect,
)
from sqlalchemy.types import TIMESTAMP, String, TypeDecorator


class PathType(TypeDecorator):
    """Custom type for a database string field with path behaviour."""

    impl = String(1024)
    cache_ok = True

    @override
    def process_bind_param(self, value: Path | None, dialect: Dialect) -> str | None:
        return str(value) if value is not None else None

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> Path | None:
        return Path(value) if value is not None else None


class UTCDatetime(TypeDecorator):
    """Custom type for a database datetime field with automatic utc conversion for sqlite3 compatibility."""

    impl = TIMESTAMP(timezone=True)
    cache_ok = True

    @override
    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return value
        return value.astimezone(UTC)

    @override
    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo:
            return value.astimezone(UTC)
        return value.replace(tzinfo=UTC)
