Validation Utilities
====================

The Lback framework provides dedicated utilities to help you validate various types of data, ensuring the integrity and correctness of input across your application. This section covers general-purpose validation tools that can be used independently of, or in conjunction with, the framework's Forms system.

---

1. ``ValidationError`` Exception
----------------------------------

At the core of the validation system is the **ValidationError** exception. This custom exception is raised whenever a piece of data fails to meet specified validation rules. It's designed to provide clear, actionable feedback about what went wrong.

.. code-block:: python

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

**Key Features:**

* ``message``: A user-friendly string describing the validation failure (e.g., "Password must be at least 8 characters long.").
* ``code`` **(Optional)**: A machine-readable string identifier for the error (e.g., ``"password_too_short"``, ``"missing_field"``). This is useful for programmatic error handling, internationalization, or distinguishing between different types of errors.

**Usage Example:**

.. code-block:: python

    from lback.utils.validation import ValidationError

    def check_age(age: int):
        if age < 18:
            raise ValidationError("You must be at least 18 years old.", code="too_young")
        print("Age is valid.")

    try:
        check_age(15)
    except ValidationError as e:
        print(f"Validation failed: {e.message} (Code: {e.code})")
        # Output: Validation failed: You must be at least 18 years old. (Code: too_young)

---

2. ``PasswordValidator``
-------------------------

The ``PasswordValidator`` class offers robust methods to enforce strong password policies. It allows you to check for common security requirements such as minimum length, presence of uppercase, lowercase, digits, and special characters.

.. code-block:: python

    import logging
    import re

    logger = logging.getLogger(__name__)

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
                raise ValidationError("Password cannot be empty.", code="empty_password")

            if len(password) < 8:
                logger.warning("Password validation failed: Password too short.")
                raise ValidationError("Password must be at least 8 characters long.", code="password_too_short")
            if not any(char.isupper() for char in password):
                logger.warning("Password validation failed: Missing uppercase letter.")
                raise ValidationError("Password must contain at least one uppercase letter.", code="no_uppercase")
            if not any(char.islower() for char in password):
                logger.warning("Password validation failed: Missing lowercase letter.")
                raise ValidationError("Password must contain at least one lowercase letter.", code="no_lowercase")
            if not any(char.isdigit() for char in password):
                logger.warning("Password validation failed: Missing digit.")
                raise ValidationError("Password must contain at least one digit.", code="no_digit")
            special_chars_pattern = r"[!@#$%^&*()_+=\-\[\]{};':\"\\|,.<>\/?~`]"
            if not re.search(special_chars_pattern, password):
                logger.warning("Password validation failed: Missing special character.")
                raise ValidationError(f"Password must contain at least one special character.", code="no_special_char")

            logger.debug("Password passed complexity validation.")

**Usage Example:**

.. code-block:: python

    from lback.utils.validation import PasswordValidator, ValidationError

    validator = PasswordValidator()

    try:
        validator.validate("StrongP@ssw0rd")
        print("Password is valid!")
    except ValidationError as e:
        print(f"Password validation failed: {e.message}")

    try:
        validator.validate("weakpass")
    except ValidationError as e:
        print(f"Password validation failed: {e.message}")
        # Output: Password validation failed: Password must be at least 8 characters long.

---

3. JSON Data Validation (``validate_json``)
--------------------------------------------

The ``validate_json`` utility function is designed to check the structure and data types of JSON payloads received in requests, which is crucial for API endpoints. It ensures that all required fields are present and that both required and optional fields conform to their expected types.

.. code-block:: python

    import logging
    # Assuming ValidationError is imported or defined in the same module
    # from .validation import ValidationError

    logger = logging.getLogger(__name__)

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
            raise ValidationError("Invalid JSON format", code="invalid_json_format")

        for field, expected_type in required_fields.items():
            if field not in data:
                logger.error(f"Missing required field: {field}")
                raise ValidationError(f"Missing required field: {field}", code="missing_field")
            if not isinstance(data[field], expected_type):
                logger.error(f"Invalid type for field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}")
                raise ValidationError(f"Invalid type for field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}", code="invalid_type")

        if optional_fields:
            for field, expected_type in optional_fields.items():
                if field in data and not isinstance(data[field], expected_type):
                    logger.error(f"Invalid type for optional field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}")
                    raise ValidationError(f"Invalid type for optional field '{field}'. Expected {expected_type.__name__}, got {type(data[field]).__name__}", code="invalid_type")

        logger.info("JSON validation successful.")
        return data

**Arguments:**

* ``request``: The request object, which is expected to have a ``parsed_body`` attribute containing the JSON data (e.g., parsed by a Body Parsing Middleware).
* ``required_fields`` (``dict``): A dictionary where keys are field names (strings) and values are the expected Python types (e.g., ``str``, ``int``, ``list``, ``dict``).
* ``optional_fields`` (``dict``, optional): Similar to ``required_fields``, but for fields that may or may not be present in the JSON data. If an optional field *is* present, its type will be validated.

**Return Value:**

* Returns the **validated** ``dict`` of data if all checks pass.

**Raises:**

* ``ValidationError``: If the JSON format is incorrect, a required field is missing, or any field has an unexpected type.

**Usage Example:**

.. code-block:: python

    from lback.utils.validation import validate_json, ValidationError
    # Assuming `request` is an object with a `parsed_body` attribute
    # For demonstration, let's mock a request object:
    class MockRequest:
        def __init__(self, body_data):
            self.parsed_body = body_data

    # Example 1: Valid data
    request_data_1 = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    req_1 = MockRequest(request_data_1)

    try:
        validated_data_1 = validate_json(
            req_1,
            required_fields={"name": str, "age": int},
            optional_fields={"email": str}
        )
        print("Validated Data 1:", validated_data_1)
        # Output: Validated Data 1: {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}
    except ValidationError as e:
        print(f"Validation failed 1: {e.message}")

    # Example 2: Missing required field
    request_data_2 = {"name": "Bob", "email": "bob@example.com"}
    req_2 = MockRequest(request_data_2)

    try:
        validate_json(
            req_2,
            required_fields={"name": str, "age": int},
            optional_fields={"email": str}
        )
    except ValidationError as e:
        print(f"Validation failed 2: {e.message} (Code: {e.code})")
        # Output: Validation failed 2: Missing required field: age (Code: missing_field)

    # Example 3: Invalid type for a field
    request_data_3 = {"name": "Charlie", "age": "thirty"}
    req_3 = MockRequest(request_data_3)

    try:
        validate_json(
            req_3,
            required_fields={"name": str, "age": int}
        )
    except ValidationError as e:
        print(f"Validation failed 3: {e.message} (Code: {e.code})")
        # Output: Validation failed 3: Invalid type for field 'age'. Expected int, got str (Code: invalid_type)

---

These validation utilities provide a solid foundation for maintaining data quality and security within your Lback application. You can integrate them into your views, API endpoints, or any part of your application logic where data integrity is paramount.