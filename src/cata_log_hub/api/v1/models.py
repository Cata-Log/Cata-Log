import enum
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator
from pydantic.fields import FieldInfo
from pydantic.types import AwareDatetime, NonNegativeInt, PositiveInt, StringConstraints
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo
from pydantic_extra_types.cron import CronStr
from sqlalchemy import sql

from cata_log_hub import constants
from cata_log_hub.api.mixins import AwareDatetimesMixin
from cata_log_hub.exceptions import (
    ProviderInvalidConfigurationWarning,
    ProviderUnknownClassWarning,
)
from cata_log_hub.providers import Provider as ProviderType


class OrderChoices(enum.StrEnum):
    """Enum subclass for ordering with sql."""

    @property
    def sql(self) -> sql.ColumnExpressionArgument:
        """Translate into sql.

        Returns:
            SQL expression for proper ordering by the string.
        """
        if self.value.startswith("-"):
            return sql.desc(self.value[1:])
        return sql.text(self.value)


class AwareTimestampsMixin(AwareDatetimesMixin):
    """Mixin for api data with aware datetimes and database timestamps."""

    created_at: AwareDatetime
    updated_at: AwareDatetime


class Catalog(AwareTimestampsMixin, BaseModel):
    """Catalog data model."""

    id: int
    provider_id: int
    valid_since: AwareDatetime
    valid_until: AwareDatetime


class CatalogOrderChoices(OrderChoices):
    """Choices for ordering catalogs."""

    ID = "id"
    VALID_SINCE = "valid_since"
    VALID_UNTIL = "valid_until"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DESC_ID = "-id"
    DESC_VALID_SINCE = "-valid_since"
    DESC_VALID_UNTIL = "-valid_until"
    DESC_CREATED_AT = "-created_at"
    DESC_UPDATED_AT = "-updated_at"


class FullCatalog(Catalog):
    """Full catalog data model."""

    pages: list[Page]


class PageFile(AwareTimestampsMixin, BaseModel):
    """Page file data model."""

    id: int
    sha256: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9]{64}$")
    ]
    size: PositiveInt
    width: PositiveInt
    height: PositiveInt
    name: str


class Page(AwareTimestampsMixin, BaseModel):
    """Page data model."""

    id: int
    number: NonNegativeInt
    catalog_id: int
    file: PageFile


class PageOrderChoices(OrderChoices):
    """Choices for ordering pages."""

    ID = "id"
    NUMBER = "number"
    CATALOG_ID = "catalog_id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DESC_ID = "-id"
    DESC_NUMBER = "-number"
    DESC_CATALOG_ID = "-catalog_id"
    DESC_CREATED_AT = "-created_at"
    DESC_UPDATED_AT = "-updated_at"


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


class Provider(AwareTimestampsMixin, BaseModel):
    """Provider data model."""

    id: int
    class_uid: str
    note: str | None
    configuration: dict[str, Any]
    status: constants.StatusEnum
    job: Job | None


class ProviderOrderChoices(OrderChoices):
    """Choices for ordering providers."""

    ID = "id"
    CLASS_UID = "class_uid"
    NOTE = "note"
    CONFIGURATION = "configuration"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DESC_ID = "-id"
    DESC_CLASS_UID = "-class_uid"
    DESC_NOTE = "-note"
    DESC_CONFIGURATION = "-configuration"
    DESC_STATUS = "-status"
    DESC_CREATED_AT = "-created_at"
    DESC_UPDATED_AT = "-updated_at"


class FullProvider(Provider):
    """Full provider data model."""

    catalogs: list[Catalog]


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
