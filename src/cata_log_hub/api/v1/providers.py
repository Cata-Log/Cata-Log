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
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from apscheduler.job import Job as SchedulerJob
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, HTTPException, Path, Query, responses, status
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import paginate as paginate_list
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic.fields import FieldInfo
from pydantic.types import AwareDatetime, NonNegativeInt, StringConstraints
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo
from pydantic_extra_types.cron import CronStr
from sqlalchemy.orm import Session, selectinload

from cata_log_hub import constants, database
from cata_log_hub.api import common
from cata_log_hub.api.mixins import AwareDatetimesMixin, AwareTimestampsMixin
from cata_log_hub.exceptions import (
    ProviderInvalidConfigurationWarning,
    ProviderUnknownClassWarning,
)
from cata_log_hub.providers import Provider as ProviderType
from cata_log_hub.scheduler import scheduler
from cata_log_hub.utils.queries import latest_provider_catalog_id_subquery, order_sql

from .catalogs import Catalog
from .pages import Page
from .pagination import PaginationPage

router = APIRouter(prefix="/providers", tags=["providers"])


class Provider(AwareTimestampsMixin, BaseModel):
    """Provider data model."""

    id: int
    class_uid: str
    note: str | None
    configuration: dict[str, Any]
    status: constants.StatusEnum
    job: Job | None


class FullProvider(Provider):
    """Full provider data model."""

    catalogs: list[Catalog]


class Job(AwareDatetimesMixin, BaseModel):
    """Job data model."""

    id: str
    next_run_time: AwareDatetime | None = None
    schedule: CronStr | None = Field(validation_alias="trigger")
    jitter: int = Field(validation_alias="trigger")

    @field_validator("schedule", mode="before")
    @classmethod
    def get_schedule_from_trigger(cls, trigger: BaseTrigger) -> str | None:
        """Get the crontab schedule as a string."""
        if isinstance(trigger, CronTrigger):
            return "{minute} {hour} {day} {month} {day_of_week}".format(
                **{field.name: str(field) for field in trigger.fields}
            )
        return None

    @field_validator("jitter", mode="before")
    @classmethod
    def get_jitter_from_trigger(cls, trigger: BaseTrigger) -> int:
        """Get the crontab schedule as a string."""
        return (trigger.jitter if isinstance(trigger, CronTrigger) else 0) or 0


class ProviderUpdate(BaseModel):
    """Provider update data model."""

    configuration: dict[str, Any] = {}
    note: str = ""

    @field_validator("configuration")
    @classmethod
    def validate_configuration(
        cls, configuration: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        """Validate the provider specific configuration."""
        class_uid = info.context.get("class_uid") if info.context else None
        if class_uid:
            try:
                provider_class = ProviderType.get_class(class_uid)
            except ProviderUnknownClassWarning as unknown_warning:
                raise PydanticCustomError(
                    "unknown_provider", str(unknown_warning)
                ) from unknown_warning
            try:
                configuration = provider_class.validate_configuration(
                    configuration
                ).model_dump()  # this won't throw a ProviderUnknownWarning since class_uid is already validated
            except ProviderInvalidConfigurationWarning as invalid_warning:
                raise invalid_warning.__cause__ or PydanticCustomError(
                    "invalid_configuration", str(invalid_warning)
                ) from invalid_warning
        return configuration


class NewProvider(BaseModel):
    """Provider creation data model."""

    # keep this order for correct order of validation steps
    class_uid: str
    configuration: dict[str, Any]
    note: str | None = None

    @field_validator("class_uid")
    @classmethod
    def validate_class_uid(cls, class_uid: str) -> str:
        """Validate the provider class uid."""
        try:
            ProviderType.get_class(class_uid)
        except ProviderUnknownClassWarning as unknown_warning:
            raise PydanticCustomError(
                "unknown_provider", str(unknown_warning)
            ) from unknown_warning
        return class_uid

    @field_validator("configuration")
    @classmethod
    def validate_configuration(
        cls, configuration: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        """Validate the provider specific configuration."""
        class_uid = info.data.get("class_uid")
        if class_uid:
            try:
                configuration = (
                    ProviderType.get_class(class_uid)
                    .validate_configuration(configuration)
                    .model_dump()
                )  # this won't throw a ProviderUnknownWarning since class_uid is already validated
            except ProviderInvalidConfigurationWarning as invalid_warning:
                raise invalid_warning.__cause__ or PydanticCustomError(
                    "invalid_configuration", str(invalid_warning)
                ) from invalid_warning
        return configuration


class RegionInfo(BaseModel):
    """Region info data model."""

    local_name: str
    language_code: str
    timezone: str

    @field_validator("timezone", mode="before")
    @classmethod
    def get_timezone_name(cls, timezone: ZoneInfo) -> str:
        """Get timezone's name."""
        return timezone.key


class ConfigInfo(BaseModel):
    """Configuration info data model."""

    description: str = ""
    default: str | None = None
    type: str = Field(validation_alias="annotation")

    @field_validator("type", mode="before")
    @classmethod
    def get_type_name(cls, annotation: type) -> str:  # type: ignore [valid-type] # mypy misinterprets type here
        """Get the type name of the config."""
        return annotation.__name__

    @field_validator("default", mode="before")
    @classmethod
    def convert_default(cls, default: str | None) -> str | None:
        """Convert default to string."""
        return str(default) if default is not None else default


class ProviderInfo(BaseModel):
    """Provider info data model."""

    name: str
    description: str
    url: str
    region: RegionInfo
    schedule: CronStr
    jitter: int
    class_uid: str = Field(validation_alias="uid")
    configuration: dict[str, ConfigInfo] = Field(validation_alias="Configuration")

    @field_validator("configuration", mode="before")
    @classmethod
    def get_configuration_schema(
        cls, configuration_class: type[ProviderType.Configuration]
    ) -> dict[str, FieldInfo]:
        """Get the config field infos from the configuration model."""
        return configuration_class.model_fields


@router.get(
    "", response_model=PaginationPage[Provider], operation_id="list-providers-v1"
)
def list_providers(
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "class_uid"
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
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/available",
    response_model=PaginationPage[ProviderInfo],
    operation_id="list-available-providers-v1",
)
def list_available_providers(
    query: Annotated[
        list[str] | None,
        StringConstraints(strip_whitespace=True, to_lower=True),
        "Filter by text (case-insensitive)",
    ] = None,
    region: Annotated[
        list[str] | None,
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
            or (
                region
                and any(
                    region_name in catalog_class.region.local_name.lower()
                    for region_name in region
                )
            )
            or (
                query
                and (
                    any(
                        query_text in catalog_class.uid.lower()
                        or query_text in catalog_class.description.lower()
                        for query_text in query
                    )
                )
            )
        ]
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Provider,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": common.HTTPStatusError,
            "description": "Object already exists.",
        },
    },
    operation_id="setup-provider-v1",
)
def post_provider(
    new_provider: NewProvider, db_session: Session = database.depends_db_session
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


# def validate_configuration(provider_id:Annotated[int, Path(description="ID of the provider")], provider_update: ProviderUpdate) -> ProviderUpdate:


@router.patch(
    "/{provider_id}",
    response_model=Provider,
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
    if "configuration" in provider_update.model_dump(exclude_unset=True):
        try:
            provider_update = ProviderUpdate.model_validate(
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
    response_model=FullProvider,
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
    response_model=ProviderInfo,
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
    response_model=PaginationPage[Catalog],
    operation_id="list-provider-catalogs-v1",
)
def list_provider_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all catalogs of a provider."""
    return paginate(
        db_session.query(database.Catalog)
        .options(selectinload(database.Catalog.pages))
        .filter(database.Catalog.provider_id == provider_id)
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/latest",
    response_model=Catalog,
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
    response_model=PaginationPage[Page],
    operation_id="get-latest-provider-catalog-pages-v1",
)
def list_latest_provider_catalog_pages(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "number"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Page]:
    """Get the pages of the latest catalog of a provider."""

    return paginate(
        db_session.query(database.Page)
        .filter(
            database.Page.catalog_id == latest_provider_catalog_id_subquery(provider_id)
        )
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/latest/pages/{page_number}",
    response_model=Page,
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
    response_model=Page,
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
    response_model=Page,
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
    response_model=PaginationPage[Catalog],
    operation_id="list-provider-current-catalogs-v1",
)
def list_provider_current_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
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
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/previews",
    response_model=PaginationPage[Catalog],
    operation_id="list-provider-preview-catalogs-v1",
)
def list_provider_preview_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all preview catalogs of a provider."""
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/{provider_id}/catalogs/outdated",
    response_model=PaginationPage[Catalog],
    operation_id="list-provider-outdated-catalogs-v1",
)
def list_provider_outdated_catalogs(
    provider_id: Annotated[int, Path(description="ID of the provider")],
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all outdated catalogs of a provider."""
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_sql(order_param) for order_param in order])
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
    response_model=Job,
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
    response_model=Provider,
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
    response_model=Provider,
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
    response_model=Job,
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
