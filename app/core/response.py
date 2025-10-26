from __future__ import annotations
from typing import Any, Optional, Dict

class ErrorCodes:
    USER_EXISTS = "USER_EXISTS"
    AUTH_FAILED = "AUTH_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    INVALID_ORDER = "INVALID_ORDER"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DUPLICATE = "DUPLICATE"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class BaseHTTPException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}

    def to_response(self, lang: str = "uz"):
        return {
            "success": False,
            "data": None,
            "error": {"code": self.code, "message": self.message, "details": self.details},
            "meta": {"lang": lang},
        }

def base_success(data: Any = None, lang: str = "uz", pagination: dict | None = None, trace_id: str | None = None):
    meta: dict = {"lang": lang}
    if pagination:
        meta["pagination"] = pagination
    if trace_id:
        meta["trace_id"] = trace_id
    return {"success": True, "data": data, "error": None, "meta": meta}
