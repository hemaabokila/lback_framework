import logging
import traceback
from http import HTTPStatus
from typing import Any

from .signals import dispatcher 
from .response import Response, HTMLResponse
from .config import Config
from .templates import TemplateRenderer
from .router import Router

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Handles application errors and exceptions, generating appropriate responses.
    Provides specific handlers for common HTTP errors (404, 405, 500) and unhandled exceptions.
    Integrates SignalDispatcher to emit events whenever an error response is generated.
    """

    def __init__(self, config: Config, template_renderer: TemplateRenderer, router: Router):
        """
        Initializes the ErrorHandler.
        Emits 'error_handler_initialized' signal.
        """
        if not isinstance(config, Config):
             logger.error("ErrorHandler initialized without a valid Config instance.")

        if not isinstance(template_renderer, TemplateRenderer):
             logger.error("ErrorHandler initialized without a valid TemplateRenderer instance.")

        if not isinstance(router, Router):
             logger.error("ErrorHandler initialized without a valid Router instance.")

        self.config = config
        self.template_renderer = template_renderer
        self.router = router
        self.logger = logging.getLogger(__name__)

        logger.info("ErrorHandler initialized.")
        dispatcher.send("error_handler_initialized", sender=self)
        logger.debug("Signal 'error_handler_initialized' sent.")

    def handle_404(self, request: Any) -> Response:
        """
        Handles 404 Not Found errors.
        Generates a 404 response, potentially with debug information in DEBUG mode.
        Emits 'error_response_generated' signal with status 404.

        Args:
            request: The incoming request object.

        Returns:
            An HTMLResponse with status 404.
        """
        status_code = HTTPStatus.NOT_FOUND.value
        error_message = "Not Found"
        self.logger.warning(f"{status_code} Error: Path '{getattr(request, 'path', 'N/A')}' not found. Method: {getattr(request, 'method', 'N/A')}")

        response = None

        if self.config.DEBUG:
            context = {
                'request_method': getattr(request, 'method', 'N/A'),
                'request_path': getattr(request, 'path', 'N/A'),
                'request_headers': dict(getattr(request, 'headers', {})),
                'routes': self.router.routes
            }
            try:
                debug_html = self.template_renderer.render_to_string("debug_404.html", **context)
                response = HTMLResponse(content=debug_html, status_code=status_code)
                self.logger.debug("Rendered debug 404 page.")
            except Exception as render_error:
                self.logger.exception("Failed to render debug 404 page template.", exc_info=render_error)
                pass
        if response is None:
            generic_404_html = """
<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #c0392b; }
    </style>
</head>
<body>
    <h1>404 Not Found</h1>
    <p>The requested resource was not found on this server.</p>
</body>
</html>
"""
            response = HTMLResponse(content=generic_404_html, status_code=status_code)
            self.logger.debug("Generated generic 404 page.")
        dispatcher.send("error_response_generated", sender=self, status_code=status_code, error_message=error_message, request=request, response=response)
        self.logger.debug(f"Signal 'error_response_generated' sent for 404 error.")

        return response
    

    def handle_403(self, request: Any, message: str = "Forbidden: You do not have permission to access this resource.") -> Response:
        """
        Handles 403 Forbidden errors.
        Generates a 403 response, potentially with debug information in DEBUG mode.
        Emits 'error_response_generated' signal with status 403.

        Args:
            request: The incoming request object.
            message: The specific message to display for the forbidden error.

        Returns:
            An HTMLResponse with status 403.
        """
        status_code = HTTPStatus.FORBIDDEN.value
        error_message = "Forbidden"
        self.logger.warning(f"{status_code} Error: Access denied for path '{getattr(request, 'path', 'N/A')}'. User: {getattr(request.user, 'username', 'N/A')}")

        response = None

        if self.config.DEBUG:
            context = {
                'request_method': getattr(request, 'method', 'N/A'),
                'request_path': getattr(request, 'path', 'N/A'),
                'request_headers': dict(getattr(request, 'headers', {})),
                'error_message': message,
                'user': getattr(request, 'user', None),
            }
            try:
                debug_html = self.template_renderer.render_to_string("debug_403.html", **context)
                response = HTMLResponse(content=debug_html, status_code=status_code)
                self.logger.debug("Rendered debug 403 page.")
            except Exception as render_error:
                self.logger.exception("Failed to render debug 403 page template. Falling back to generic.", exc_info=render_error)
                pass

        if response is None:
            generic_403_html = """
<!DOCTYPE html>
<html>
<head>
    <title>403 Forbidden</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #dc3545; }
        p { color: #495057; }
    </style>
</head>
<body>
    <h1>403 Forbidden</h1>
    <p>{message}</p>
    <p>You do not have permission to access this resource.</p>
</body>
</html>
"""
            response = HTMLResponse(content=generic_403_html, status_code=status_code)
            self.logger.debug("Generated generic 403 page.")

        dispatcher.send("error_response_generated", sender=self, status_code=status_code, error_message=message, request=request, response=response)
        self.logger.debug(f"Signal 'error_response_generated' sent for 403 error.")

        return response

    def handle_500(self, error: Exception) -> Response:
        """
        Handles generic 500 Internal Server Errors (explicitly raised 500).
        Generates a generic 500 response.
        Emits 'error_response_generated' signal with status 500.

        Args:
            error: The exception object that caused the 500 error.

        Returns:
            An HTMLResponse with status 500.
        """
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        error_message = "Internal Server Error"
        self.logger.error(f"{status_code} Error: Internal Server Error (Explicitly raised)", exc_info=error)

        generic_500_html = """
<!DOCTYPE html>
<html>
<head>
    <title>500 Internal Server Error</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #c0392b; }
    </style>
</head>
<body>
    <h1>500 Internal Server Error</h1>
    <p>An unexpected error occurred on the server. Please try again later.</p>
</body>
</html>
"""
        response = HTMLResponse(content=generic_500_html, status_code=status_code)
        self.logger.debug("Generated generic 500 page.")
        dispatcher.send("error_response_generated", sender=self, status_code=status_code, error_message=error_message, exception=error, response=response)
        self.logger.debug(f"Signal 'error_response_generated' sent for 500 error.")

        return response

    def handle_custom_error(self, status_code: int, message: str) -> Response:
        """
        Handles custom errors with a specific status code and message.
        Generates a custom error response.
        Emits 'error_response_generated' signal with the custom status code.

        Args:
            status_code: The HTTP status code for the error.
            message: The custom error message.

        Returns:
            An HTMLResponse with the custom status code.
        """
        self.logger.error(f"Custom Error {status_code}: {message}")

        custom_error_html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Error {status_code}</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #c0392b; }
    </style>
</head>
<body>
    <h1>Error {status_code}</h1>
    <p>{message}</p>
</body>
</html>
"""
        custom_error_html = custom_error_html_template.format(status_code=status_code, message=message)
        response = HTMLResponse(content=custom_error_html, status_code=status_code)
        self.logger.debug(f"Generated custom error page with status {status_code}.")
        dispatcher.send("error_response_generated", sender=self, status_code=status_code, error_message=message, response=response)
        self.logger.debug(f"Signal 'error_response_generated' sent for custom error {status_code}.")

        return response

    def handle_405(self, request: Any, allowed_methods: list) -> Response:
        """
        Handles 405 Method Not Allowed errors.
        Generates a 405 response, potentially with debug information in DEBUG mode.
        Emits 'error_response_generated' signal with status 405.

        Args:
            request: The incoming request object.
            allowed_methods: A list of allowed HTTP methods for the requested path.

        Returns:
            An HTMLResponse with status 405 and an 'Allow' header.
        """
        status_code = HTTPStatus.METHOD_NOT_ALLOWED.value
        error_message = "Method Not Allowed"
        allowed_methods_str = ", ".join(allowed_methods)
        self.logger.warning(f"{status_code} Error: Method '{getattr(request, 'method', 'N/A')}' not allowed for path '{getattr(request, 'path', 'N/A')}'. Allowed: {allowed_methods_str}")

        response = None
        headers = {"Allow": allowed_methods_str}

        if self.config.DEBUG:
            context = {
                'request_method': getattr(request, 'method', 'N/A'),
                'request_path': getattr(request, 'path', 'N/A'),
                'allowed_methods': allowed_methods,
                'request_headers': dict(getattr(request, 'headers', {})),
            }
            try:
                debug_html = self.template_renderer.render_to_string("debug_405.html", **context)
                response = HTMLResponse(content=debug_html, status_code=status_code, headers=headers)
                self.logger.debug("Rendered debug 405 page.")
            except Exception as render_error:
                self.logger.exception("Failed to render debug 405 page template.", exc_info=render_error)
                pass

        if response is None:
            generic_405_html = """
<!DOCTYPE html>
<html>
<head>
    <title>405 Method Not Allowed</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #c0392b; }
    </style>
</head>
<body>
    <h1>405 Method Not Allowed</h1>
    <p>The requested method is not allowed for this URL.</p>
</body>
</html>
"""
            response = HTMLResponse(content=generic_405_html, status_code=status_code, headers=headers)
            self.logger.debug("Generated generic 405 page.")

        dispatcher.send("error_response_generated", sender=self, status_code=status_code, error_message=error_message, request=request, allowed_methods=allowed_methods, response=response)
        self.logger.debug(f"Signal 'error_response_generated' sent for 405 error.")

        return response


    def handle_exception(self, exception: Exception, request: Any) -> Response:
        """
        Handles unhandled exceptions that occur during request processing.
        Generates a 500 response, potentially with detailed debug information in DEBUG mode.
        Emits 'unhandled_exception_response_generated' signal.

        Args:
            exception: The unhandled exception object.
            request: The incoming request object.

        Returns:
            An HTMLResponse with status 500.
        """
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        error_message = "Internal Server Error"
        self.logger.error("Unhandled Exception during request processing.", exc_info=exception)

        response = None

        if self.config.DEBUG:
            exception_type = type(exception).__name__
            exception_message = str(exception)

            tb_list = traceback.extract_tb(exception.__traceback__)
            traceback_frames = []
            for frame in tb_list:
                 traceback_frames.append({
                     'filename': frame.filename,
                     'lineno': frame.lineno,
                     'name': frame.name,
                     'line': frame.line if frame.line else 'N/A',
                 })

            context = {
                'exception_type': exception_type,
                'exception_message': exception_message,
                'traceback_frames': traceback_frames,
                'request_method': getattr(request, 'method', 'N/A'),
                'request_path': getattr(request, 'path', 'N/A'),
                'request_headers': dict(getattr(request, 'headers', {})),
                'request_body': getattr(request, 'body', b'').decode('utf-8', errors='ignore') if getattr(request, 'body', None) else '',
            }

            try:
                debug_html = self.template_renderer.render_to_string("debug_error.html", **context)
                response = HTMLResponse(content=debug_html, status_code=status_code)
                self.logger.debug("Rendered debug exception page.")
            except Exception as render_error:
                self.logger.exception("Failed to render debug error page template.", exc_info=render_error)
                fallback_html_template_base = """
<!DOCTYPE html>
<html>
<head>
    <title>Internal Server Error - Debug Page Rendering Failed</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #c0392b; }
    </style>
</head>
<body>
    <h1>Internal Server Error</h1>
    <p>An error occurred while trying to render the debug error page.</p>
"""
                fallback_html_template_debug_details = """<p>Original Error Details: {exception_type}: {exception_message}</p>"""
                fallback_html_template_end = """</body></html>"""

                fallback_html = fallback_html_template_base
                if self.config.DEBUG:
                     fallback_html += fallback_html_template_debug_details.format(exception_type=exception_type, exception_message=exception_message)
                fallback_html += fallback_html_template_end

                response = HTMLResponse(content=fallback_html, status_code=status_code)
                self.logger.debug("Generated fallback debug exception page.")


        if response is None:
            generic_500_html = """
<!DOCTYPE html>
<html>
<head>
    <title>500 Internal Server Error</title>
    <style> body { font-family: sans-serif; text-align: center; margin-top: 50px; } h1 { color: #c0392b; } </style>
</head>
<body>
    <h1>500 Internal Server Error</h1>
    <p>An unexpected error occurred. Please try again later.</p>
</body>
</html>
"""
            response = HTMLResponse(content=generic_500_html, status_code=status_code)
            self.logger.debug("Generated generic 500 page for unhandled exception.")

        dispatcher.send("unhandled_exception_response_generated", sender=self, status_code=status_code, exception=exception, request=request, response=response)
        self.logger.debug(f"Signal 'unhandled_exception_response_generated' sent for unhandled exception.")

        return response
