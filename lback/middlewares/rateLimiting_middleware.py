import logging
from typing import Optional
from http import HTTPStatus

from lback.core.base_middleware import BaseMiddleware
from lback.core.types import Request
from lback.core.response import Response
from lback.security.rate_limiter import RateLimiter 

logger = logging.getLogger(__name__)

class RateLimitingMiddleware(BaseMiddleware):
    """
    Middleware to apply rate limiting to incoming requests using a RateLimiter instance.
    Takes a RateLimiter instance as a dependency.
    """
    def __init__(self, rate_limiter: RateLimiter):
        """
        Initializes with a RateLimiter instance.
        Args:
            rate_limiter: An instance of RateLimiter, configured with max requests and window.
            (a dependency).
        """
        self.rate_limiter = rate_limiter
        logger.info("RateLimitingMiddleware initialized.")

    def process_request(self, request: Request) -> Optional[Response]:
        """
        Applies rate limiting check to the incoming request.
        Returns a 429 Too Many Requests response if the limit is exceeded.
        """
        request_method = getattr(request, 'method', 'N/A')
        request_path = getattr(request, 'path', 'N/A')
        logger.debug(f"RateLimitingMiddleware: Checking rate limit for {request_method} {request_path}.")
        client_ip = request.client_addr if hasattr(request, 'client_addr') and request.client_addr else request.environ.get('REMOTE_ADDR', 'N/A')
        if client_ip is None or client_ip == 'N/A':
            logger.debug("RateLimitingMiddleware: Could not determine client IP. Skipping IP-based rate limiting.")
            return None 
        if not self.rate_limiter.is_allowed(client_ip):
            logger.warning(f"RateLimitingMiddleware: Rate limit exceeded for IP: {client_ip}")
            return Response(
                body=b"Too Many Requests",
                status_code=HTTPStatus.TOO_MANY_REQUESTS.value,
                headers={'Content-Type': 'text/plain'}
            )
        logger.debug(f"RateLimitingMiddleware: Request allowed for IP: {client_ip}")
        return None

    def process_response(self, request: Request, response: Response) -> Response:
        logger.debug("RateLimitingMiddleware: Processing response (no changes made).")
        return response