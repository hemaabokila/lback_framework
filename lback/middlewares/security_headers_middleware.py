import logging
from typing import Optional

from lback.core.base_middleware import BaseMiddleware
from lback.core.types import Request
from lback.core.response import Response
from lback.security.headers import SecurityHeadersConfigurator 


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseMiddleware):
    """
    Middleware to add security headers to responses based on application configuration.
    Takes a SecurityHeadersConfigurator instance as a dependency.
    """
    def __init__(self, headers_configurator: SecurityHeadersConfigurator):
        """
        Initializes with a SecurityHeadersConfigurator instance.
        Args:
            headers_configurator: An instance of SecurityHeadersConfigurator,
            configured with application settings (a dependency).
        """
        self.headers_configurator = headers_configurator
        logger.info("SecurityHeadersMiddleware initialized.")
    def process_request(self, request: Request) -> Optional[Response]:
        """
        Processes the request (this middleware doesn't modify requests).
        """
        logger.debug("SecurityHeadersMiddleware: Processing request (no-op).")
        return None
    def process_response(self, request: Request, response: Response) -> Response:
        """
        Adds security headers to the response by getting them from the configurator.
        """
        logger.debug(f"SecurityHeadersMiddleware: Processing response (status: {response.status_code}).")
        headers_to_add = self.headers_configurator.get_headers()
        if hasattr(response, 'headers') and isinstance(response.headers, dict):
            response.headers.update(headers_to_add) 
            logger.debug("SecurityHeadersMiddleware: Added security headers to response.")
        elif hasattr(response, 'headers') and isinstance(response.headers, list):
            logger.warning("SecurityHeadersMiddleware: Response headers is a list, cannot update directly with update(). Skipping header addition.")
        else:
            logger.error("SecurityHeadersMiddleware: Response object does not have a 'headers' attribute or it's not a dictionary. Cannot add security headers.")
        logger.debug("SecurityHeadersMiddleware: Finished processing response.")
        return response
