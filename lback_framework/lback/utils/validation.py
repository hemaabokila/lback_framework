import logging
import re

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message="Validation error occurred"):
        super().__init__(message)


class PasswordValidator:
    """
    Provides methods to validate password complexity.
    """
    def validate(self, password: str):
        """
        Validates the complexity of a given password.

        Args:
            password: The plain text password to validate.

        Raises:
            ValidationError: If the password does not meet complexity requirements.
        """
        if not password or not isinstance(password, str) or len(password.strip()) == 0:
            logger.warning("Password validation failed: Password is empty.")
            raise ValidationError("Password cannot be empty.")

        if len(password) < 8:
            logger.warning("Password validation failed: Password too short.")
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in password):
            logger.warning("Password validation failed: Missing uppercase letter.")
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            logger.warning("Password validation failed: Missing lowercase letter.")
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            logger.warning("Password validation failed: Missing digit.")
            raise ValidationError("Password must contain at least one digit.")
        special_chars = r"[!@#$%^&*()_+=\-\[\]{};':\"\\|,.<>\/?~`]"
        if not re.search(special_chars, password):
            logger.warning("Password validation failed: Missing special character.")
            raise ValidationError(f"Password must contain at least one special character from: {special_chars}")
        
        logger.debug("Password passed complexity validation.")

def validate_json(request, required_fields: dict, optional_fields: dict = None):
    """
    Validate JSON data in the request.

    Args:
        request: The request object containing parsed_body.
        required_fields (dict): A dictionary of required fields and their expected types.
        optional_fields (dict): A dictionary of optional fields and their expected types.

    Returns:
        dict: The validated data.

    Raises:
        ValidationError: If validation fails.
    """
    data = request.parsed_body
    if not isinstance(data, dict):
        logger.error("Invalid JSON format.")
        raise ValidationError("Invalid JSON format")

    for field, expected_type in required_fields.items():
        if field not in data:
            logger.error(f"Missing required field: {field}")
            raise ValidationError(f"Missing required field: {field}")
        if not isinstance(data[field], expected_type):
            logger.error(f"Invalid type for field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}")
            raise ValidationError(f"Invalid type for field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}")

    if optional_fields:
        for field, expected_type in optional_fields.items():
            if field in data and not isinstance(data[field], expected_type):
                logger.error(f"Invalid type for optional field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}")
                raise ValidationError(f"Invalid type for optional field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}")

    logger.info("JSON validation successful.")
    return data