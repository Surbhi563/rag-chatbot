"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class BaseServiceException(Exception):
    """Base exception for all service-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseServiceException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class NotFoundError(BaseServiceException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
        )


class ExternalServiceError(BaseServiceException):
    """Raised when an external service call fails."""
    
    def __init__(self, service: str, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(
            message=f"External service '{service}' error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code},
        )


class DatabaseError(BaseServiceException):
    """Raised when a database operation fails."""
    
    def __init__(self, operation: str, message: str) -> None:
        super().__init__(
            message=f"Database {operation} failed: {message}",
            error_code="DATABASE_ERROR",
            details={"operation": operation},
        )
