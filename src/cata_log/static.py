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

from importlib import resources

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cata_log.settings import settings

app = FastAPI(openapi_url=None)

app.mount("/pages", StaticFiles(directory=settings.storage_path), name="static-pages")

with resources.path("cata_log.web", "static/js") as path:
    app.mount(
        "/js",
        StaticFiles(directory=path),
        name="static-js",
    )
