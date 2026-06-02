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

from fastapi import Depends, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse

from cata_log_hub import (
    __version__,
    api,
    health,
    opds,
    security,
    static,
    web,
)
from cata_log_hub.api import common


def create_fastapi_app() -> FastAPI:
    """Create an instance of the Cata-Log fastapi app.

    Returns:
        The fastapi app.
    """
    app = FastAPI(
        dependencies=[Depends(security.verify_credentials)],
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "model": common.HTTPStatusError,
                "description": "Request is not authorized",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "model": common.HTTPValidationError,
                "description": "Request failed to validate",
            },
        },
        exception_handlers={
            RequestValidationError: common.validation_exception_handler
        },
        title="Cata-Log",
        description="The Central Hub For Grocery Store Catalogs",
        summary="API overview for Cata-Log",
        version=__version__,
        license_info={
            "name": "AGPL version 3 or later",
            "url": "https://www.gnu.org/licenses/agpl-3.0",
        },
        contact={
            "name": "Github Repo",
            "url": "https://github.com/cata-log/cata-log-hub.git",
        },
        docs_url="/docs/swagger",
        redoc_url="/docs/redoc",
    )

    app.add_route(
        "/docs",
        lambda _: RedirectResponse("/docs/swagger", status_code=status.HTTP_302_FOUND),
    )
    app.mount("/static", static.create_staticfiles_app(), "static")
    app.include_router(api.router)
    app.include_router(web.router)
    app.include_router(opds.router)
    app.include_router(health.router)

    return app
