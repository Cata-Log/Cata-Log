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

from pydantic import BaseModel


class HTTPStatusError(BaseModel):
    """Basic response data model for a HTTP status error."""

    detail: str


class HTTP400ErrorDetail(BaseModel):
    """Model for HTTP 400 error detail data."""

    message: str
    fields: list[dict[str, str | list[str]]]


class HTTP400Error(BaseModel):
    """Response data model for a HTTP 400 error."""

    detail: HTTP400ErrorDetail
