import logging
from typing import Optional
from http import HTTPStatus

from lback.core.base_middleware import BaseMiddleware
from lback.core.types import Request
from lback.core.response import Response
from lback.security.sql_injection import SQLInjectionProtection


logger = logging.getLogger(__name__)


class SQLInjectionDetectionMiddleware(BaseMiddleware):
    """
    Middleware to detect potential SQL injection attempts in request body and query parameters.
    """
    def __init__(self):
        """
        Initializes the SQLInjectionDetectionMiddleware.
        Note: This middleware uses class methods from SQLInjectionProtection,
        so it doesn't require an instance of that class.
        """
        logger.info("SQLInjectionDetectionMiddleware initialized.")
    def process_request(self, request: Request) -> Optional[Response]:
        """
        Checks request body and query parameters for suspicious SQL injection patterns.
        Returns a 400 Bad Request response if patterns are detected.
        """
        request_method = getattr(request, 'method', 'N/A')
        request_path = getattr(request, 'path', 'N/A')
        logger.debug(f"SQLInjectionDetectionMiddleware: Checking request from {request_method} {request_path} for injection patterns.")

        if request.parsed_body: 
            logger.debug("SQLInjectionDetectionMiddleware: Validating request body.")
            if not SQLInjectionProtection.validate_inputs(request.parsed_body):
                logger.warning(f"SQLInjectionDetectionMiddleware: Suspicious pattern detected in request body for {request_method} {request_path}.")
                return Response(
                    body=b"Bad Request: Potential SQL Injection attempt detected.",
                    status_code=HTTPStatus.BAD_REQUEST.value,
                    headers={'Content-Type': 'text/plain'}
                )
            logger.debug("SQLInjectionDetectionMiddleware: Request body validation passed.")

        if request.query_params:
            logger.debug("SQLInjectionDetectionMiddleware: Validating query parameters.")
            if not SQLInjectionProtection.validate_inputs(request.query_params):
                logger.warning(f"SQLInjectionDetectionMiddleware: Suspicious pattern detected in query parameters for {request_method} {request_path}.")
                return Response(
                    body=b"Bad Request: Potential SQL Injection attempt detected in query parameters.",
                    status_code=HTTPStatus.BAD_REQUEST.value,
                    headers={'Content-Type': 'text/plain'}
                )
            logger.debug("SQLInjectionDetectionMiddleware: Query parameters validation passed.")
        logger.debug("SQLInjectionDetectionMiddleware: Request passed injection detection checks. Continuing chain.")
        return None
    def process_response(self, request: Request, response: Response) -> Response:
        logger.debug("SQLInjectionDetectionMiddleware: Processing response (no changes made).")
        return response