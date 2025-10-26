from pydantic import BaseModel, Field
from typing import Any, Optional, Dict

class ErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class BaseResponse(BaseModel):
    success: bool = True
    data: Any | None = None
    error: ErrorDetails | None = None
    meta: dict | None = None
