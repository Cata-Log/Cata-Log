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

from fastapi import Response, status
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session, selectinload

from cata_log import database

router = APIRouter(prefix="/opds", tags=["opds"])

__all__ = ["router"]


@router.get("/")
def get_opds_catalog_overview(
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the odps overview."""
    catalogs = (
        db_session.query(database.Catalog)
        .options(
            selectinload(database.Catalog.provider),
            selectinload(database.Catalog.pages),
        )
        .order_by(database.Catalog.created_at.desc())
        .all()
    )
    opds_xml = f"""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:opds="http://opds-spec.org/2010/catalog">
      <title>Cata-Log Library</title>
      <id>opds-root</id>
      <updated>{datetime.now(tz=UTC).isoformat(timespec="seconds")}</updated>
      """
    for catalog in catalogs:
        provider_class = catalog.provider.get_provider_class()
        opds_xml += f"""
        <entry>
            <title>{catalog.provider.class_id.title()} {catalog.valid_since.date()} - {catalog.valid_until.date()}</title>
            <id>{catalog.id}</id>
            <summary>{provider_class.description}</summary>
            <dc:language>{provider_class.region.language_code}</dc:language>
            <dc:publisher>{catalog.provider.class_id.title()}</dc:publisher>
            <dc:issued>{catalog.created_at.date().isoformat()}</dc:issued>
            <updated>{catalog.updated_at.isoformat(timespec="seconds")}</updated>
            <link rel="http://opds-spec.org/image/thumbnail"
                  href="/api/v1/pages/{catalog.pages[0].id}/download"
                  type="{catalog.pages[0].media_type}" />
            <link href="/opds/{catalog.id}.epub"
                rel="http://opds-spec.org/acquisition"
                type="application/epub+zip"/>
            <link href="/api/v1/catalogs/{catalog.id}/download"
                rel="http://opds-spec.org/acquisition"
                type="application/pdf"/>
        </entry>
        """
    opds_xml += "</feed>"
    return Response(content=opds_xml, media_type="application/atom+xml")


@router.get("/{catalog_id}.epub")
def get_catalog_epub(
    catalog_id: int, db_session: Session = database.depends_db_session
) -> Response:
    """Get a single catalog as epub."""
    catalog = db_session.get(
        database.Catalog,
        catalog_id,
        options=[
            selectinload(database.Catalog.pages),
            selectinload(database.Catalog.provider),
        ],
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    return Response(
        content=catalog.as_epub(),
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'attachment; filename="{catalog_id}.epub"'},
    )
