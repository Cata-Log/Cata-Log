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

from sqlalchemy import ScalarSelect, sql
from sqlalchemy.sql import ColumnExpressionArgument

from cata_log import database


def latest_provider_catalog_id_subquery(provider_id: int) -> ScalarSelect[int]:
    """Create a subquery for the id of the latest catalog of a provider.

    Args:
        provider_id: The id of the provider.

    Returns:
        A subquery to use in sql queries that need the latest provider catalog id.
    """
    return (
        sql.select(database.Catalog.id)
        .filter(database.Catalog.provider_id == provider_id)
        .order_by(database.Catalog.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )


def order_sql(string: str) -> ColumnExpressionArgument:
    """Translates an ordering string into sql.

    Args:
        string: The string to translate.

    Returns:
        SQL expression for proper ordering by the string.
    """
    if string.startswith("-"):
        return sql.desc(string[1:])
    return sql.text(string)
