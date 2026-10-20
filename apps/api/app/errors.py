from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from apps.api.app.logging import get_logger, request_id_var
from apps.api.app.schemas.common import ErrorOut

logger = get_logger("apps.api.errors")


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        hint: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.hint = hint
        self.headers = headers or {}
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", hint: Optional[str] = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, hint=hint)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required", hint: Optional[str] = "Provide valid credentials or Bearer token"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
            hint=hint,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access forbidden", hint: Optional[str] = "You do not have access to this resource"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, hint=hint)


class ValidationError(AppException):
    def __init__(self, message: str = "Invalid input data", hint: Optional[str] = None):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422, hint=hint)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict", hint: Optional[str] = None):
        super().__init__(code="CONFLICT", message=message, status_code=409, hint=hint)


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded", hint: Optional[str] = "Slow down your requests and retry"):
        super().__init__(code="RATE_LIMITED", message=message, status_code=429, hint=hint)


class DegradedServiceError(AppException):
    def __init__(self, message: str = "Service degraded or unavailable", hint: Optional[str] = None):
        super().__init__(code="SERVICE_DEGRADED", message=message, status_code=503, hint=hint)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = request_id_var.get() or request.headers.get("X-Request-ID")
        error_payload = ErrorOut(
            code=exc.code,
            message=exc.message,
            hint=exc.hint,
            request_id=req_id,
        ).model_dump()
        logger.warning(f"Handled AppException: {exc.code} - {exc.message} [status={exc.status_code}]")
        return JSONResponse(status_code=exc.status_code, content=error_payload, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = request_id_var.get() or request.headers.get("X-Request-ID")
        errors = exc.errors()
        first_err = errors[0] if errors else {}
        loc = " -> ".join(str(l) for l in first_err.get("loc", []))
        msg = first_err.get("msg", "Invalid request body")
        formatted_message = f"{loc}: {msg}" if loc else msg
        error_payload = ErrorOut(
            code="REQUEST_VALIDATION_ERROR",
            message=formatted_message,
            hint="Check API documentation for the required payload format",
            request_id=req_id,
        ).model_dump()
        return JSONResponse(status_code=422, content=error_payload)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = request_id_var.get() or request.headers.get("X-Request-ID")
        error_payload = ErrorOut(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            hint=None,
            request_id=req_id,
        ).model_dump()
        return JSONResponse(status_code=exc.status_code, content=error_payload, headers=exc.headers)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = request_id_var.get() or request.headers.get("X-Request-ID")
        logger.exception(f"Unhandled server error: {exc}")
        error_payload = ErrorOut(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred",
            hint="Inspect server logs using the request_id",
            request_id=req_id,
        ).model_dump()
        return JSONResponse(status_code=500, content=error_payload)
