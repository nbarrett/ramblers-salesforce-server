from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .models import ApiError, ApiErrorCode, ApiErrorResponse

STATUS_BY_CODE: dict[str, int] = {
    "UNAUTHORIZED": 401,
    "GROUP_NOT_FOUND": 404,
    "MEMBER_NOT_FOUND": 404,
    "BAD_REQUEST": 400,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
}


class ApiException(Exception):
    def __init__(
        self, code: ApiErrorCode, message: str, details: Optional[dict[str, object]] = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    @property
    def status_code(self) -> int:
        return STATUS_BY_CODE.get(self.code, 500)

    def to_response(self) -> ApiErrorResponse:
        return ApiErrorResponse(
            error=ApiError(code=self.code, message=self.message, details=self.details),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
