"""
Standardized API Error Handling - FortexaRH
Custom exceptions and error response model for consistent API errors.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
    path: Optional[str] = None


class AppError(Exception):
    """Base application error."""
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(detail=detail, status_code=404)


class AuthenticationError(AppError):
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(detail=detail, status_code=401)


class AuthorizationError(AppError):
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(detail=detail, status_code=403)


class ValidationError(AppError):
    def __init__(self, detail: str = "Datos invalidos"):
        super().__init__(detail=detail, status_code=422)


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflicto de datos"):
        super().__init__(detail=detail, status_code=409)


class RateLimitError(AppError):
    def __init__(self, detail: str = "Demasiadas solicitudes"):
        super().__init__(detail=detail, status_code=429)


async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )
