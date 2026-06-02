from typing import TypeVar, override

from fastapi import Query
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import RawParams
from fastapi_pagination.customization import (
    CustomizedPage,
    UseFieldsAliases,
    UseFieldTypeAnnotations,
    UseName,
    UseParams,
)
from fastapi_pagination.types import GreaterEqualZero

from cata_log_hub.settings import get_settings

T = TypeVar("T")


class PaginationParams(Params):
    """Queryparameters model for pagination."""

    page: int = Query(0, ge=0, description="Pagination page number")
    size: int = Query(
        get_settings().api_default_pagination_page_size,
        ge=1,
        le=get_settings().api_max_pagination_page_size,
        description="Pagination page size",
    )

    @override
    def to_raw_params(self) -> RawParams:
        raw_params = super().to_raw_params()
        if raw_params.offset is not None and raw_params.limit is not None:
            raw_params.offset += raw_params.limit
        return raw_params


PaginationPage = CustomizedPage[
    Page[T],
    UseParams(PaginationParams),
    UseName("PaginationPage"),
    UseFieldsAliases(items="results"),
    UseFieldTypeAnnotations(page=GreaterEqualZero),
]
