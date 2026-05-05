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

import alembic.command
from alembic.config import Config
from fastapi import Depends, FastAPI, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from cata_log import (
    __version__,
    api,
    constants,
    health,
    jobs,
    logging,
    opds,
    security,
    settings,
    web,
)
from cata_log.exceptions import HealthCheckFailedError

logging.setup_logging()

settings.Settings.check()

alembic_config = Config("cata_log/migrations/alembic.ini")
alembic.command.upgrade(config=alembic_config, revision="head")

jobs.scheduler.start()

app = FastAPI(
    dependencies=[Depends(security.verify_credentials)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": security.HTTP401Error,
            "description": "If the request is not authorized.",
        },
    },
    title=constants.FAST_API_TITLE,
    description=constants.FAST_API_DESCRIPTION,
    summary=constants.FAST_API_SUMMARY,
    version=__version__.code,
    license_info=constants.FAST_API_LICENSE_INFO,
    contact=constants.FAST_API_CONTACT,
    docs_url="/docs/swagger",
    redoc_url="/docs/redoc",
)
app.add_route(
    "/docs",
    lambda _: RedirectResponse("/docs/swagger", status_code=status.HTTP_302_FOUND),
)
app.mount(
    "/static/pages", StaticFiles(directory=constants.STORAGE_PATH), name="static_pages"
)
app.mount(
    "/static/js",
    StaticFiles(directory=constants.SOURCE_PATH / "cata_log/web/static/js"),
    name="static-js",
)


@app.get("/health", status_code=200)
def healthcheck() -> None:
    """HTTP endpoint to trigger healthchecks."""
    try:
        health.check()
    except HealthCheckFailedError as error:
        raise HTTPException(detail=str(error), status_code=500) from error
    else:
        return


app.include_router(api.router)
app.include_router(web.router)
app.include_router(opds.router)
