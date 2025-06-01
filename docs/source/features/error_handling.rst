Error Handling and HTTP Exceptions
==================================

Robust error handling is crucial for any web application. The Lback Framework provides a structured way to manage exceptions, especially those related to HTTP responses, allowing you to return meaningful error messages and status codes to clients. This section details the core exception classes provided by the framework and how to use them.

---

1. Base Exception Classes
-------------------------

All framework-specific exceptions in Lback inherit from a common base, ensuring a consistent approach to error management.

.. code-block:: python

    from typing import Any, Dict, Optional, List

    class FrameworkException(Exception):
        """
        Base exception for all framework-specific errors.
        All custom exceptions in the framework should inherit from this.
        """
        pass

    class HTTPException(FrameworkException):
        """
        Base exception for HTTP-related errors.
        When raised, it typically results in an HTTP response with a specific status code.
        """
        status_code = 500
        message = "An unexpected error occurred."
        data: Optional[Any] = None

        def __init__(self, message: Optional[str] = None, status_code: Optional[int] = None, data: Optional[Any] = None):
            self.message = message if message is not None else self.__class__.message
            self.status_code = status_code if status_code is not None else self.__class__.status_code
            self.data = data if data is not None else self.__class__.data
            super().__init__(self.message)

**FrameworkException**:

This is the top-level exception for all custom errors originating from the Lback Framework. It provides a common parent for catching any framework-specific issues.

**HTTPException**:

This is the base class for all exceptions that should result in a specific HTTP response being sent back to the client. It includes attributes to define the **HTTP status code**, a **message** for the client, and optional **additional data** that can be included in the error response (e.g., validation errors).

* **status_code**: The HTTP status code (e.g., 200, 400, 404, 500) associated with the error.
* **message**: A human-readable message describing the error.
* **data**: Optional extra data (e.g., a dictionary of validation errors) to be included in the error response payload.

You can raise ``HTTPException`` directly for generic HTTP errors, or use its specialized subclasses for more specific scenarios.

---

2. Common HTTP Exception Subclasses
------------------------------------

The framework provides several pre-defined ``HTTPException`` subclasses for common HTTP error scenarios. Using these specific exceptions makes your code clearer and helps the framework handle responses appropriately.

.. code-block:: python

    class BadRequest(HTTPException):
        status_code = 400
        message = "Bad Request"

        def __init__(self, message: Optional[str] = None, data: Optional[Any] = None):
            super().__init__(message=message, status_code=400, data=data)
            if data is not None and message is None:
                self.message = "Validation failed." # Default message if data (errors) is provided

    class NotFound(HTTPException):
        status_code = 404
        message = "Not Found"

        def __init__(self, message: Optional[str] = None, data: Optional[Any] = None):
            super().__init__(message=message, data=data)

    class RouteNotFound(NotFound):
        message = "Route Not Found"

        def __init__(self, path: str, method: str, message: Optional[str] = None):
            super().__init__(message=message, data=None)
            self.path = path
            self.method = method
            if message is None:
                self.message = f"No route found for {method} {path}"

    class Unauthorized(HTTPException):
        status_code = 401
        message = "Unauthorized"

        def __init__(self, message: Optional[str] = None, data: Optional[Any] = None):
            super().__init__(message=message, status_code=401, data=data)

    class Forbidden(HTTPException):
        status_code = 403
        message = "Forbidden"

        def __init__(self, message: Optional[str] = None, data: Optional[Any] = None):
            super().__init__(message=message, status_code=403, data=data)

    class MethodNotAllowed(HTTPException):
        status_code = 405
        message = "Method Not Allowed"

        def __init__(self, path: str, method: str, allowed_methods: list, message: Optional[str] = None):
            super().__init__(message=message, status_code=405, data=None)
            self.path = path
            self.method = method
            self.allowed_methods = allowed_methods
            if message is None:
                self.message = f"Method {method} not allowed for path {path}. Allowed methods: {', '.join(allowed_methods)}"

    class ServerError(HTTPException):
        status_code = 500
        message = "Internal Server Error"

        def __init__(self, message: Optional[str] = None, data: Optional[Any] = None):
            super().__init__(message=message, status_code=500, data=data)

    class ConfigurationError(FrameworkException):
        """
        Raised when there's an issue with the application's configuration.
        """
        pass

    class ValidationError(BadRequest): # Inherits from BadRequest (HTTP 400)
        status_code = 400
        message = "Validation Error"

        def __init__(self, errors: Dict[str, List[str]], message: Optional[str] = None):
            super().__init__(message=message, status_code=400, data=errors)
            if self.message is None:
                self.message = "Validation failed."
            self.errors = errors # Specific attribute to hold validation details

Here's a breakdown of the commonly used HTTP exception classes:

* ``BadRequest(message: Optional[str], data: Optional[Any])`` **(Status: 400 Bad Request)**:
    Used when the server cannot process the request due to client error (e.g., malformed syntax, invalid request parameters). If ``data`` is provided (e.g., a dictionary of validation errors), the default message will be "Validation failed.".

* ``NotFound(message: Optional[str], data: Optional[Any])`` **(Status: 404 Not Found)**:
    Indicates that the requested resource could not be found on the server.

* ``RouteNotFound(path: str, method: str, message: Optional[str])`` **(Status: 404 Not Found)**:
    A specialized `NotFound` exception, automatically populated with details about the requested path and method when no matching route is found.

* ``Unauthorized(message: Optional[str], data: Optional[Any])`` **(Status: 401 Unauthorized)**:
    Signifies that authentication is required or has failed. This typically means the client needs to provide valid authentication credentials.

* ``Forbidden(message: Optional[str], data: Optional[Any])`` **(Status: 403 Forbidden)**:
    Indicates that the server understood the request but refuses to authorize it. This implies that the client's credentials (if any) are valid, but they do not have permission to access the resource.

* ``MethodNotAllowed(path: str, method: str, allowed_methods: list, message: Optional[str])`` **(Status: 405 Method Not Allowed)**:
    Raised when the HTTP method used in the request (e.g., POST) is not supported for the resource identified by the URL. It automatically includes the allowed methods.

* ``ServerError(message: Optional[str], data: Optional[Any])`` **(Status: 500 Internal Server Error)**:
    A general-purpose error message, used when an unexpected condition was encountered on the server. This should ideally be caught and handled, but serves as a fallback for uncaught exceptions.

* ``ConfigurationError``:
    This ``FrameworkException`` (not an ``HTTPException``) is specifically for issues related to the application's setup or settings.

* ``ValidationError(errors: Dict[str, List[str]], message: Optional[str])`` **(Status: 400 Bad Request)**:
    A crucial exception for data validation. It inherits from ``BadRequest`` and is specifically designed to carry detailed validation error messages, typically as a dictionary where keys are field names and values are lists of error strings for that field.

---

3. Raising and Handling Exceptions
----------------------------------

You can raise these exceptions directly within your views, middlewares, or utility functions. The framework's core request handling mechanism is designed to catch ``HTTPException`` instances and convert them into appropriate HTTP responses.

**Example: Raising a** ``BadRequest`` **for invalid input**

.. code-block:: python

    from lback.exceptions import BadRequest
    from lback.utils.validation import validate_json, ValidationError # Assuming your validation utilities are imported

    def create_user_view(request):
        try:
            # Attempt to validate incoming JSON data
            user_data = validate_json(
                request,
                required_fields={"username": str, "email": str, "password": str},
                optional_fields={"age": int}
            )
            # If validation passes, proceed with business logic
            # ... create user in database ...
            return Response(json={"message": "User created successfully"}, status_code=201)

        except ValidationError as e:
            # If validate_json raises ValidationError, it means the data is invalid.
            # ValidationError itself is a BadRequest, so you can re-raise it,
            # and the framework will handle it as a 400 with the error data.
            raise e # Or you could catch it and return a custom Response
        except Exception as e:
            # Catch any other unexpected errors and raise a 500
            raise ServerError(message="Failed to create user due to server issue.")


**Example: Raising** ``NotFound`` **for missing resources**

.. code-block:: python

    from lback.exceptions import NotFound

    def get_user_detail_view(request, user_id):
        user = get_user_from_db(user_id) # Assume this function fetches a user
        if user is None:
            raise NotFound(message=f"User with ID {user_id} not found.")
        return Response(json=user.to_dict())

**Framework's Default Error Handling**:

By default, when an ``HTTPException`` is raised:

* The framework intercepts it.
* It extracts the ``status_code``, ``message``, and ``data`` (if any) from the exception.
* It constructs an HTTP response with the specified status code and typically a JSON body containing ``{"detail": "Your error message here", "data": {...}}``.
* This response then proceeds through the ``process_response`` middleware chain.

For unhandled Python exceptions (not instances of ``HTTPException``), the framework will typically convert them into a ``ServerError`` **(500 Internal Server Error)** response, logging the full traceback for debugging purposes (especially when ``DEBUG`` is enabled).

---

By leveraging these exception classes, you can provide clear, standardized error responses to clients, making your API more robust and easier to consume.