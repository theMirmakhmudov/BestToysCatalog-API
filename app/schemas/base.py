from typing import Generic, TypeVar, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")

class ErrorDetails(BaseModel):
    fields: dict[str, str] | None = None

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: ErrorDetails | None = None

class PaginationMeta(BaseModel):
    limit: int
    offset: int
    count: int
    total: int

class MetaResponse(BaseModel):
    trace_id: str | None = None
    lang: str | None = None
    pagination: PaginationMeta | None = None

class BaseResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT | None = None
    error: ErrorResponse | None = None
    meta: MetaResponse | None = None
