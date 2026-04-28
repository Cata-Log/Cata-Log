from pydantic import BaseModel


class HTTPStatusError(BaseModel):
    """Basic response data model for a HTTP status error."""

    detail: str


class HTTP400ErrorDetail(BaseModel):
    """Model for HTTP 400 error detail data."""

    message: str
    fields: list[dict[str, str | list[str]]]


class HTTP400Error(BaseModel):
    """Response data model for a HTTP 400 error."""

    detail: HTTP400ErrorDetail
