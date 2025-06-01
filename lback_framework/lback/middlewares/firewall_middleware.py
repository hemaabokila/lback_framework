import logging
from typing import Optional
from http import HTTPStatus

from lback.core.base_middleware import BaseMiddleware
from lback.core.types import Request
from lback.core.response import Response
from lback.security.firewall import AdvancedFirewall

logger = logging.getLogger(__name__)

class FirewallMiddleware(BaseMiddleware):
    """
    Middleware to check incoming requests against AdvancedFirewall rules.
    """
    def __init__(self, firewall: AdvancedFirewall):
        """
        Initializes the FirewallMiddleware.
        Args:
            firewall: An instance of the AdvancedFirewall class, configured with rules.
        """
        self.firewall = firewall
        logger.info("FirewallMiddleware initialized.")
    def process_request(self, request: Request) -> Optional[Response]:
        """
        Processes the incoming request. Checks if the request is allowed by the firewall.
        Args:
            request: The incoming Request object.
        Returns:
            A Response object if the request is blocked (e.g., 403 Forbidden),
            otherwise None to allow the request to proceed.
        """
        
        client_ip = request.client_addr if hasattr(request, 'client_addr') and request.client_addr else request.environ.get('REMOTE_ADDR', 'N/A')
        user_agent = request.headers.get('User-Agent', '')
        requested_url = request.path
        
        logger.debug(f"FirewallMiddleware: Checking request from IP: {client_ip}, UA: {user_agent[:50]}, URL: {requested_url}")
        if not self.firewall.is_allowed(client_ip, user_agent, requested_url):
            logger.warning(f"FirewallMiddleware: Request blocked from IP: {client_ip}")
            return Response(
                body=b"Forbidden",
                status_code=HTTPStatus.FORBIDDEN.value,
                headers={'Content-Type': 'text/plain'}
            )
        else:
            logger.debug(f"FirewallMiddleware: Request allowed from IP: {client_ip}")
            return None 

    def process_response(self, request: Request, response: Response) -> Response:
        return response
    
