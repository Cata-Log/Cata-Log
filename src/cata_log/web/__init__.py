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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from cata_log import database
from cata_log.constants import DefaultConfig
from cata_log.providers import Provider

router = APIRouter(prefix="", tags=["web"])


__all__ = ["router"]

templates = Jinja2Templates(directory="cata_log/web/templates")


@router.get("/", response_class=HTMLResponse)
def get_dash(request: Request) -> HTMLResponse:
    """Get the web interface."""
    return templates.TemplateResponse(request, name="dash.html.jinja")


@router.get("/providers", response_class=HTMLResponse)
def get_providers(request: Request) -> HTMLResponse:
    """Get the providers web interface."""
    available_providers = [
        catalog_class.info() for catalog_class in Provider.get_classes()
    ]
    with database.DBSession() as db_session:
        providers = db_session.query(database.Provider).all()

    return templates.TemplateResponse(
        request,
        name="providers.html.jinja",
        context={"available_providers": available_providers, "providers": providers},
    )


@router.get("/config", response_class=HTMLResponse)
def get_config(request: Request) -> HTMLResponse:
    """Get the web interface."""
    default_configs = list(DefaultConfig)
    with database.DBSession() as db_session:
        configs = db_session.query(database.Config).all()
    return templates.TemplateResponse(
        request,
        name="config.html.jinja",
        context={"default_configs": default_configs, "configs": configs},
    )
