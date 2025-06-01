from typing import Any, Dict, Optional, List

class FrameworkException(Exception):
    pass

class HTTPException(FrameworkException):
    status_code = 500
    message = "An unexpected error occurred."
    data: Optional[Any] = None

    def __init__(self, message: Optional[str] = None, status_code: Optional[int] = None, data: Optional[Any] = None):
        self.message = message if message is not None else self.__class__.message
        self.status_code = status_code if status_code is not None else self.__class__.status_code
        self.data = data if data is not None else self.__class__.data
        super().__init__(self.message)

class BadRequest(HTTPException):
    status_code = 400
    message = "Bad Request"

    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(message=message, status_code=400, data=data)
        if data is not None and message is None:
            self.message = "Validation failed."

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
    pass

class ValidationError(BadRequest):
    status_code = 400
    message = "Validation Error"

    def __init__(self, errors: Dict[str, List[str]], message: Optional[str] = None):
        super().__init__(message=message, status_code=400, data=errors)
        if self.message is None:
            self.message = "Validation failed."
        self.errors = errors
