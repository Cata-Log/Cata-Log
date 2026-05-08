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
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from cata_log import (
    __version__,
    api,
    health,
    opds,
    security,
    static,
    web,
)
from cata_log.api import common
from cata_log.exceptions import HealthCheckFailedError

app = FastAPI(
    dependencies=[Depends(security.verify_credentials)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": common.HTTPStatusError,
            "description": "If the request is not authorized.",
        },
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
        "url": "https://github.com/cata-log/cata-log.git",
    },
    docs_url="/docs/swagger",
    redoc_url="/docs/redoc",
)
app.add_route(
    "/docs",
    lambda _: RedirectResponse("/docs/swagger", status_code=status.HTTP_302_FOUND),
)


@app.get("/health", status_code=200, include_in_schema=False)
def healthcheck() -> None:
    """HTTP endpoint to trigger healthchecks."""
    try:
        health.check()
    except HealthCheckFailedError as error:
        raise HTTPException(detail=str(error), status_code=500) from error


app.mount("/static", static.app, "static")
app.include_router(api.router)
app.include_router(web.router)
app.include_router(opds.router)
