"""
Error handling utilities for secure error responses.
"""
import logging
from typing import Any, Dict
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class SecureErrorHandler:
    """Handles errors securely by logging details but returning generic messages to clients."""
    
    @staticmethod
    def log_and_raise_generic(
        error: Exception,
        user_message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        context: Dict[str, Any] = None
    ) -> None:
        """
        Log detailed error information and raise a generic HTTPException.
        
        Args:
            error: The original exception
            user_message: Generic message to show to user
            status_code: HTTP status code to return
            context: Additional context for logging
        """
        # Log detailed error for debugging
        context_str = f" Context: {context}" if context else ""
        logger.error(f"Error occurred: {str(error)}{context_str}", exc_info=True)
        
        # Raise generic error for client
        raise HTTPException(
            status_code=status_code,
            detail=user_message
        )
    
    @staticmethod
    def log_and_raise_auth_error(
        error: Exception,
        operation: str = "authentication",
        context: Dict[str, Any] = None
    ) -> None:
        """Handle authentication-related errors."""
        SecureErrorHandler.log_and_raise_generic(
            error=error,
            user_message=f"Authentication failed. Please try again.",
            status_code=status.HTTP_400_BAD_REQUEST,
            context={**(context or {}), "operation": operation}
        )
    
    @staticmethod
    def log_and_raise_validation_error(
        error: Exception,
        field: str = None,
        context: Dict[str, Any] = None
    ) -> None:
        """Handle validation errors."""
        message = f"Invalid {field}" if field else "Invalid input"
        SecureErrorHandler.log_and_raise_generic(
            error=error,
            user_message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            context={**(context or {}), "field": field}
        )
    
    @staticmethod
    def log_and_raise_not_found(
        error: Exception,
        resource: str = "resource",
        context: Dict[str, Any] = None
    ) -> None:
        """Handle not found errors."""
        SecureErrorHandler.log_and_raise_generic(
            error=error,
            user_message=f"{resource.title()} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            context={**(context or {}), "resource": resource}
        )
    
    @staticmethod
    def log_and_raise_permission_error(
        error: Exception,
        action: str = "perform this action",
        context: Dict[str, Any] = None
    ) -> None:
        """Handle permission errors."""
        SecureErrorHandler.log_and_raise_generic(
            error=error,
            user_message=f"Permission denied to {action}",
            status_code=status.HTTP_403_FORBIDDEN,
            context={**(context or {}), "action": action}
        )


# Convenience functions
def handle_auth_error(error: Exception, operation: str = "authentication", **context):
    """Convenience function for authentication errors."""
    SecureErrorHandler.log_and_raise_auth_error(error, operation, context)

def handle_validation_error(error: Exception, field: str = None, **context):
    """Convenience function for validation errors."""
    SecureErrorHandler.log_and_raise_validation_error(error, field, context)

def handle_not_found_error(error: Exception, resource: str = "resource", **context):
    """Convenience function for not found errors."""
    SecureErrorHandler.log_and_raise_not_found(error, resource, context)

def handle_permission_error(error: Exception, action: str = "perform this action", **context):
    """Convenience function for permission errors."""
    SecureErrorHandler.log_and_raise_permission_error(error, action, context)

def handle_generic_error(error: Exception, message: str = "An error occurred", **context):
    """Convenience function for generic errors."""
    SecureErrorHandler.log_and_raise_generic(error, message, context=context)
