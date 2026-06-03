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
from typing import Annotated

from apscheduler.job import Job as SchedulerJob
from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, HTTPException, Path, Query, responses, status
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import paginate as paginate_list
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import ValidationError
from pydantic.types import NonNegativeInt, StringConstraints
from sqlalchemy.orm import Session, selectinload

from cata_log_hub import database
from cata_log_hub.api import common
from cata_log_hub.exceptions import (
    ProviderUnknownClassWarning,
)
from cata_log_hub.providers import Provider as ProviderType
from cata_log_hub.scheduler import scheduler
from cata_log_hub.utils.queries import latest_provider_catalog_id_subquery

from . import models
from .pagination import PaginationPage

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get(
    "", response_model=PaginationPage[models.Provider], operation_id="list-providers-v1"
)
def list_providers(
    order: Annotated[
        list[models.ProviderOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.ProviderOrderChoices.CLASS_UID
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Provider]:
    """List all providers."""
    return paginate(
        db_session.query(database.Provider)
        .options(
            selectinload(database.Provider.catalogs).selectinload(
                database.Catalog.pages
            )
        )
        .order_by(*[order_param.sql(database.Provider) for order_param in order])
    )


@router.get(
    "/available",
    response_model=PaginationPage[models.ProviderInfo],
    operation_id="list-available-providers-v1",
)
def list_available_providers(
    query: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, to_lower=True),
        "Filter by text (case-insensitive)",
    ] = None,
    region: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, to_lower=True),
        "Filter by region local name (case-insensitive)",
    ] = None,
) -> PaginationPage[type[ProviderType]]:
    """List all available providers."""
    return paginate_list(
        [
            catalog_class
            for catalog_class in ProviderType.get_classes()
            if (not query and not region)
            or (region and region in catalog_class.region.local_name.lower())
            or (
                query
                and (
                    query in catalog_class.uid.lower()
                    or query in catalog_class.description.lower()
                )
            )
        ]
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=models.Provider,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": common.HTTPStatusError,
            "description": "Object already exists.",
        },
    },
    operation_id="setup-provider-v1",
)
def post_provider(
    new_provider: models.NewProvider, db_session: Session = database.depends_db_session
) -> database.Provider:
    """Set up a new provider."""
    if any(
        existing_provider.configuration == new_provider.configuration
        for existing_provider in db_session.query(database.Provider)
        .filter(database.Provider.class_uid == new_provider.class_uid)
        .all()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The given provider configuration already exists",
        )
    provider = database.Provider(
        **new_provider.model_dump(),
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    scheduler.add_job(
        "cata_log_hub.jobs:fetch_provider",
        args=[provider.id],
        trigger=DateTrigger(),
        id=f"fetch-provider-{provider.id}-on-post-one-off",
        replace_existing=True,
    )
    return provider


@router.patch(
    "/{provider_id}",
    response_model=models.Provider,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
        status.HTTP_409_CONFLICT: {
            "model": common.HTTPStatusError,
            "description": "Object already exists.",
        },
    },
    operation_id="update-provider-v1",
)
def patch_provider(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    provider_update: models.ProviderUpdate,
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
    if "configuration" in provider_update.model_dump(exclude_unset=True):
        try:
            provider_update = models.ProviderUpdate.model_validate(
                provider_update.model_dump(), context={"class_uid": provider.class_uid}
            )
        except ValidationError as validation_error:
            raise RequestValidationError(
                validation_error.errors()
            ) from validation_error
        if any(
            other_provider.configuration == provider_update.configuration
            for other_provider in db_session.query(database.Provider)
            .filter(database.Provider.class_uid == provider.class_uid)
            .filter(database.Provider.id != provider.id)
            .all()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The given provider configuration already exists",
            )
    for key, value in provider_update.model_dump(exclude_unset=True).items():
        setattr(provider, key, value)
    db_session.commit()
    scheduler.add_job(
        "cata_log_hub.jobs:fetch_provider",
        args=[provider_id],
        trigger=DateTrigger(),
        id=f"fetch-provider-{provider.id}-on-patch-one-off",
        replace_existing=True,
    )
    return provider


@router.get(
    "/{provider_id}",
    response_model=models.FullProvider,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="get-provider-v1",
)
def get_provider(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
) -> database.Provider:
    """Get a single provider."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return provider


@router.get(
    "/available/{provider_class_uid}",
    response_model=models.ProviderInfo,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="get-available-provider-v1",
)
def get_available_provider(
    provider_class_uid: Annotated[str, Path(description="Class UID of the provider")],
) -> type[ProviderType]:
    """Get a single provider."""
    try:
        provider_class = ProviderType.get_class(provider_class_uid)
    except ProviderUnknownClassWarning as warning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not available"
        ) from warning
    return provider_class


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="delete-provider-v1",
)
def delete_provider(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
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
    response_model=PaginationPage[models.Catalog],
    operation_id="list-provider-catalogs-v1",
)
def list_provider_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[
        list[models.CatalogOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.CatalogOrderChoices.DESC_CREATED_AT
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all catalogs of a provider."""
    return paginate(
        db_session.query(database.Catalog)
        .options(selectinload(database.Catalog.pages))
        .filter(database.Catalog.provider_id == provider_id)
        .order_by(*[order_param.sql(database.Catalog) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/latest",
    response_model=models.Catalog,
    operation_id="get-latest-provider-catalog-v1",
)
def get_latest_provider_catalog(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
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
def download_latest_provider_catalog(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
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
    "/{provider_id}/catalogs/latest/embed",
    operation_id="embed-latest-provider-catalog-v1",
)
def embed_latest_provider_catalog(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
    db_session: Session = database.depends_db_session,
) -> responses.Response:
    """Embed the latest catalog of a provider as pdf."""
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
        "Content-Disposition": f"inline; filename={filename}",
    }
    return responses.Response(
        catalog.as_pdf(), headers=headers, media_type="application/pdf"
    )


@router.get(
    "/{provider_id}/catalogs/latest/pages",
    response_model=PaginationPage[models.Page],
    operation_id="get-latest-provider-catalog-pages-v1",
)
def list_latest_provider_catalog_pages(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[
        list[models.PageOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.PageOrderChoices.NUMBER
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Page]:
    """Get the pages of the latest catalog of a provider."""

    return paginate(
        db_session.query(database.Page)
        .filter(
            database.Page.catalog_id == latest_provider_catalog_id_subquery(provider_id)
        )
        .order_by(*[order_param.sql(database.Page) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/latest/pages/{page_number}",
    response_model=models.Page,
    operation_id="get-latest-provider-catalog-page-v1",
)
def get_latest_provider_catalog_page(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    page_number: Annotated[NonNegativeInt, Path(description="Number of the page")],
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
    response_model=models.Page,
    operation_id="download-latest-provider-catalog-page-v1",
)
def download_latest_provider_catalog_page(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    page_number: Annotated[NonNegativeInt, Path(description="Number of the page")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
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
    response_model=models.Page,
    operation_id="embed-latest-provider-catalog-page-v1",
)
def embed_latest_provider_catalog_page(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    page_number: Annotated[NonNegativeInt, Path(description="Number of the page")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
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
    response_model=PaginationPage[models.Catalog],
    operation_id="list-provider-current-catalogs-v1",
)
def list_provider_current_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[
        list[models.CatalogOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.CatalogOrderChoices.DESC_CREATED_AT
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all current catalogs of a provider."""
    now = datetime.now(tz=UTC)
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since <= now)
        .filter(database.Catalog.valid_until > now)
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_param.sql(database.Catalog) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/previews",
    response_model=PaginationPage[models.Catalog],
    operation_id="list-provider-preview-catalogs-v1",
)
def list_provider_preview_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[
        list[models.CatalogOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.CatalogOrderChoices.DESC_CREATED_AT
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all preview catalogs of a provider."""
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_param.sql(database.Catalog) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/outdated",
    response_model=PaginationPage[models.Catalog],
    operation_id="list-provider-outdated-catalogs-v1",
)
def list_provider_outdated_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[
        list[models.CatalogOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.CatalogOrderChoices.DESC_CREATED_AT
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all outdated catalogs of a provider."""
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_param.sql(database.Catalog) for order_param in order])
    )


@router.post(
    "/{provider_id}/job/run",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    response_model=models.Job,
    operation_id="run-provider-job-v1",
)
def post_provider_job_run(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
) -> SchedulerJob:
    """Run the providers job to update its catalog."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return scheduler.add_job(
        "cata_log_hub.jobs:fetch_provider",
        args=[provider_id],
        trigger=DateTrigger(),
        id=f"fetch-provider-{provider_id}-user-triggered-one-off",
        replace_existing=True,
    )


@router.post(
    "/{provider_id}/job",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    response_model=models.Provider,
    operation_id="add-provider-job-v1",
)
def post_provider_add_job(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
) -> database.Provider:
    """Add the provider's job."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    provider.add_job()
    db_session.commit()
    return provider


@router.delete(
    "/{provider_id}/job",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    response_model=models.Provider,
    operation_id="delete-provider-job-v1",
)
def post_provider_remove_job(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
) -> database.Provider:
    """Remove the provider's job."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    provider.remove_job()
    db_session.commit()
    return provider


@router.get(
    "/{provider_id}/job",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    response_model=models.Job,
    operation_id="get-provider-job-v1",
)
def get_provider_job(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    db_session: Session = database.depends_db_session,
) -> SchedulerJob:
    """Remove the provider's job."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    job = provider.job
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job
