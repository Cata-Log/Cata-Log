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

from fastapi import APIRouter, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload

from cata_log import constants, database
from cata_log.providers import Provider

router = APIRouter(prefix="", tags=["web"], include_in_schema=False)


__all__ = ["router"]

templates = Jinja2Templates(directory=constants.SOURCE_PATH / "cata_log/web/templates")


@router.get("/", response_class=HTMLResponse)
def get_providers_webpage(request: Request) -> HTMLResponse:
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


@router.get("/catalogs/provider/{provider_id}/latest/", response_class=HTMLResponse)
def get_provider_catalog_webpage(request: Request, provider_id: int) -> HTMLResponse:
    """Get the latest provider catalog web interface."""
    with database.DBSession() as db_session:
        catalog = (
            db_session.query(database.Catalog)
            .filter(database.Catalog.provider_id == provider_id)
            .options(selectinload(database.Catalog.provider))
            .order_by(database.Catalog.created_at.desc())
            .first()
        )
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
            )
    return templates.TemplateResponse(
        request,
        name="latest-provider-catalog.html.jinja",
        context={
            "catalog": catalog,
        },
    )


@router.get("/catalogs/{catalog_id}/", response_class=HTMLResponse)
def get_catalog_webpage(request: Request, catalog_id: int) -> HTMLResponse:
    """Get the catalog web interface."""
    with database.DBSession() as db_session:
        catalog = db_session.get(database.Catalog, catalog_id)
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
            )
    return templates.TemplateResponse(
        request,
        name="catalog.html.jinja",
        context={
            "catalog": catalog,
        },
    )
