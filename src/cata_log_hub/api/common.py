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

from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator


class HTTPStatusError(BaseModel):
    """Basic data model for a HTTP status error response.
    Intentionally close to the FastAPI default.
    """

    detail: str


class ValidationError(BaseModel):
    """Data model for a validation error.
    Intentionally close to the pydantic default.
    """

    type: str
    loc: list[str]
    msg: str
    input: str | None = None
    ctx: str | None = None

    @field_validator("loc", mode="before")
    @classmethod
    def convert_loc(cls, loc: list[object]) -> list[str]:
        """Convert input to string."""
        return [str(loc_item) for loc_item in loc]

    @field_validator("input", mode="before")
    @classmethod
    def convert_input(cls, input: object | None) -> str | None:  # noqa: A002 # to match attribute name
        """Convert input to string."""
        return str(input) if input is not None else input

    @field_validator("ctx", mode="before")
    @classmethod
    def convert_ctx(cls, ctx: object | None) -> str | None:
        """Convert ctx to string."""
        return str(ctx) if ctx is not None else ctx


class HTTPValidationError(BaseModel):
    """Data model for a HTTP validation response.
    Intentionally close to the FastAPI default.
    """

    detail: list[ValidationError]


async def validation_exception_handler(
    request: Request,  # noqa: ARG001 # required in the signature of a FastAPI exception_handler
    exc: RequestValidationError,
) -> JSONResponse:
    """Handler for request validation errors."""
    http_validation_error = HTTPValidationError.model_validate({"detail": exc.errors()})
    return JSONResponse(
        status_code=422,
        content=http_validation_error.model_dump(),
    )
