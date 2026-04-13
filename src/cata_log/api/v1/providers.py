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

from fastapi import APIRouter, HTTPException, responses, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from starlette.responses import JSONResponse

from cata_log import constants, database
from cata_log.api.mixins import TimestampMixin
from cata_log.exceptions import (
    ProviderIncompleteConfigWarning,
    ProviderInvalidConfigWarning,
    ProviderUnknownClassWarning,
)
from cata_log.providers import Provider as ProviderType
from cata_log.tasks import fetch_provider
from cata_log.utils.queries import latest_provider_catalog_id_subquery

from .catalogs import Catalog
from .pages import Page

router = APIRouter(prefix="/providers", tags=["providers"])


class Provider(BaseModel, TimestampMixin):
    """Provider data model."""

    id: int
    class_id: str
    config: dict[str, str]
    status: constants.StatusEnum
    catalogs: list[Catalog]


class ProviderUpdate(BaseModel):
    """Provider update data model."""

    config: dict[str, str]


class NewProvider(BaseModel):
    """Provider creation data model."""

    class_id: str
    config: dict[str, str]


class RegionInfo(BaseModel):
    """Region info data model."""

    local_name: str
    language_code: str
    timezone: str


class ConfigInfo(BaseModel):
    """Configuration info data model."""

    name: str
    helptext: str
    default: str | None
    parse_as: str


class ProviderInfo(BaseModel):
    """Provider info data model."""

    id: str
    configuration: list[ConfigInfo]
    description: str
    url: str
    region: RegionInfo


@router.get("", response_model=list[Provider], operation_id="list-providers-v1")
async def list_providers(
    db_session: Session = database.depends_db_session,
) -> list[database.Provider]:
    """List all providers."""
    return (
        db_session.query(database.Provider)
        .options(
            selectinload(database.Provider.catalogs).selectinload(
                database.Catalog.pages
            )
        )
        .order_by(database.Provider.class_id)
        .all()
    )


@router.get(
    "/available",
    response_model=list[ProviderInfo],
    operation_id="list-available-providers-v1",
)
async def list_available_providers(
    query: str | None = None, region: str | None = None
) -> list[dict[str, str | dict[str, str] | list[dict[str, str | None]]]]:
    """List all available providers."""
    if region:
        region = region.lower()
    if query:
        query = query.lower()
    return [
        catalog_class.info()
        for catalog_class in ProviderType.get_classes()
        if (not query and not region)
        or (region and (region in catalog_class.region.local_name.lower()))
        or (
            query
            and (
                (query in catalog_class.id())
                or (query in catalog_class.description.lower())
            )
        )
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Provider,
    operation_id="setup-provider-v1",
)
async def post_provider(
    new_provider: NewProvider, db_session: Session = database.depends_db_session
) -> database.Provider:
    """Set up a new provider."""
    try:
        provider_class = ProviderType.get_class(new_provider.class_id)
    except ProviderUnknownClassWarning as unknown_class_warning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "The given provider type is unknown",
                "class_id": unknown_class_warning.class_id,
            },
        ) from unknown_class_warning
    try:
        validated_config = provider_class.validate_config(new_provider.config)
    except ProviderIncompleteConfigWarning as incomplete_warning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "The given provider configuration is incomplete",
                "missing_configurations": incomplete_warning.missing_configs,
            },
        ) from incomplete_warning
    except ProviderInvalidConfigWarning as invalid_warning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "The given provider configuration is invalid",
                "missing_configurations": invalid_warning.bad_configs,
            },
        ) from invalid_warning
    if any(
        provider.config == validated_config
        for provider in db_session.query(database.Provider)
        .filter(database.Provider.class_id == new_provider.class_id)
        .all()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given provider configuration already exists",
        )
    provider = database.Provider(
        **new_provider.model_dump(exclude={"config"}), config=validated_config
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    fetch_provider.delay(provider.id)
    return provider


@router.patch(
    "/{provider_id}",
    response_model=Provider,
    operation_id="update-provider-v1",
)
async def patch_provider(
    provider_id: int,
    provider_update: ProviderUpdate,
    db_session: Session = database.depends_db_session,
) -> database.Provider:
    """Update a provider."""
    provider = db_session.get(
        database.Provider,
        provider_id,
        options=[
            selectinload(database.Provider.catalogs).selectinload(
                database.Catalog.pages
            )
        ],
    )
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    try:
        provider_class = provider.get_provider_class()
    except ProviderUnknownClassWarning as unknown_class_warning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "The given provider type is unknown",
                "class_id": unknown_class_warning.class_id,
            },
        ) from unknown_class_warning
    try:
        validated_config = provider_class.validate_config(provider_update.config)
    except ProviderIncompleteConfigWarning as incomplete_warning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "The given provider configuration is incomplete",
                "missing_configurations": incomplete_warning.missing_configs,
            },
        ) from incomplete_warning
    except ProviderInvalidConfigWarning as invalid_warning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "The given provider configuration is invalid",
                "invalid_configurations": invalid_warning.bad_configs,
            },
        ) from invalid_warning
    if any(
        provider.config == validated_config
        for provider in db_session.query(database.Provider)
        .filter(database.Provider.class_id == provider.class_id)
        .filter(database.Provider.id != provider.id)
        .all()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given provider configuration already exists",
        )
    provider.config = validated_config
    db_session.commit()
    db_session.refresh(provider)
    fetch_provider.delay(provider.id)
    return provider


@router.get("/{provider_id}", response_model=Provider, operation_id="get-provider-v1")
async def get_provider(
    provider_id: int, db_session: Session = database.depends_db_session
) -> database.Provider:
    """Get a single provider."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return provider


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete-provider-v1",
)
async def delete_provider(
    provider_id: int, db_session: Session = database.depends_db_session
) -> None:
    """Delete a single provider. This also deletes all its catalogs and their pages."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    db_session.delete(provider)
    db_session.commit()


@router.get(
    "/{provider_id}/catalogs",
    response_model=list[Catalog],
    operation_id="list-provider-catalogs-v1",
)
async def list_provider_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .options(selectinload(database.Catalog.pages))
        .filter(database.Catalog.provider_id == provider_id)
        .order_by(database.Catalog.created_at.desc())
        .all()
    )


@router.get(
    "/{provider_id}/catalogs/latest",
    response_model=Catalog,
    operation_id="get-latest-provider-catalog-v1",
)
async def get_latest_provider_catalog(
    provider_id: int, db_session: Session = database.depends_db_session
) -> database.Catalog:
    """Get the latest catalog of a provider."""
    latest_catalog = (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .options(selectinload(database.Catalog.pages))
        .order_by(database.Catalog.created_at.desc())
        .first()
    )
    if not latest_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    return latest_catalog


@router.get(
    "/{provider_id}/catalogs/latest/download",
    operation_id="download-latest-provider-catalog-v1",
)
async def download_latest_provider_catalog(
    provider_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> responses.Response:
    """Download the latest catalog of a provider as pdf."""
    catalog = (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .options(selectinload(database.Catalog.pages))
        .order_by(database.Catalog.created_at.desc())
        .first()
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    filename = filename or f"catalog-{catalog.id}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return responses.Response(
        catalog.as_pdf(), headers=headers, media_type="application/pdf"
    )


@router.get(
    "/{provider_id}/catalogs/latest/pages",
    response_model=list[Page],
    operation_id="get-latest-provider-catalog-pages-v1",
)
async def list_latest_provider_catalog_pages(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Page]:
    """Get the pages of the latest catalog of a provider."""

    return (
        db_session.query(database.Page)
        .filter(
            database.Page.catalog_id == latest_provider_catalog_id_subquery(provider_id)
        )
        .order_by(database.Page.number)
        .all()
    )


@router.get(
    "/{provider_id}/catalogs/latest/pages/{page_number}",
    response_model=Page,
    operation_id="get-latest-provider-catalog-page-v1",
)
async def get_latest_provider_catalog_page(
    provider_id: int,
    page_number: int,
    db_session: Session = database.depends_db_session,
) -> database.Page:
    """Get the pages of the latest catalog of a provider."""
    page = (
        db_session.query(database.Page)
        .filter(
            database.Page.catalog_id == latest_provider_catalog_id_subquery(provider_id)
        )
        .filter(database.Page.number == page_number)
        .one_or_none()
    )
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


@router.get(
    "/{provider_id}/catalogs/latest/pages/{page_number}/download",
    response_model=Page,
    operation_id="download-latest-provider-catalog-page-v1",
)
async def download_latest_provider_catalog_page(
    provider_id: int,
    page_number: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> responses.FileResponse:
    """Download a single page of the latest catalog of a provider."""
    page_path = (
        db_session.query(database.PageFile.path)
        .join(database.Page.file)
        .filter(
            database.Page.catalog_id == latest_provider_catalog_id_subquery(provider_id)
        )
        .filter(database.Page.number == page_number)
        .scalar()
    )
    if not page_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    filename = filename or page_path.name
    return responses.FileResponse(
        path=page_path,
        filename=filename,
        content_disposition_type="attachment",
    )


@router.get(
    "/{provider_id}/catalogs/latest/pages/{page_number}/embed",
    response_model=Page,
    operation_id="embed-latest-provider-catalog-page-v1",
)
async def embed_latest_provider_catalog_page(
    provider_id: int,
    page_number: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> responses.FileResponse:
    """Embed a single page of the latest catalog of a provider."""
    page_path = (
        db_session.query(database.PageFile.path)
        .join(database.Page.file)
        .filter(
            database.Page.catalog_id == latest_provider_catalog_id_subquery(provider_id)
        )
        .filter(database.Page.number == page_number)
        .scalar()
    )
    if not page_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    filename = filename or page_path.name
    return responses.FileResponse(
        path=page_path,
        filename=filename,
        content_disposition_type="inline",
    )


@router.get(
    "/{provider_id}/catalogs/current",
    response_model=list[Catalog],
    operation_id="list-provider-current-catalogs-v1",
)
async def list_provider_current_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all current catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since <= datetime.now(tz=UTC))
        .filter(database.Catalog.valid_until > datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(database.Catalog.created_at.desc())
        .all()
    )


@router.get(
    "/{provider_id}/catalogs/previews",
    response_model=list[Catalog],
    operation_id="list-provider-preview-catalogs-v1",
)
async def list_provider_preview_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all preview catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(database.Catalog.created_at.desc())
        .all()
    )


@router.get(
    "/{provider_id}/catalogs/outdated",
    response_model=list[Catalog],
    operation_id="list-provider-outdated-catalogs-v1",
)
async def list_provider_outdated_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all outdated catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(database.Catalog.created_at.desc())
        .all()
    )


@router.post(
    "/{provider_id}/update",
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse,
    operation_id="request-provider-update-v1",
)
async def post_provider_update(
    provider_id: int, db_session: Session = database.depends_db_session
) -> dict[str, str]:
    """Trigger an update of a providers catalogs."""
    provider = db_session.get(
        database.Provider,
        provider_id,
        options=[
            selectinload(database.Provider.catalogs).selectinload(
                database.Catalog.pages
            ),
        ],
    )
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    fetch_provider.delay(provider_id)
    return {"detail": "Provider update scheduled."}
