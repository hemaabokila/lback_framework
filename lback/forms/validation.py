"""
Contains exceptions used during form and field validation.
"""
from typing import Optional
class ValidationError(Exception):
    """
    Base exception for validation errors.
    Can be raised by field or form validation methods.
    """
    def __init__(self, message: str, code: Optional[str] = None):
        """
        Initializes a ValidationError.

        Args:
            message: A human-readable error message.
            code: An optional machine-readable error code (e.g., 'required', 'invalid_email').
        """
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self) -> str:
        """String representation includes the code if available."""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

