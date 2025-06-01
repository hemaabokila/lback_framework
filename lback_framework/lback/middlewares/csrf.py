import logging
import secrets
from typing import Optional
from http import HTTPStatus

from lback.core.base_middleware import BaseMiddleware
from lback.utils.app_session import AppSession
from lback.utils.session_manager import SessionManager
from lback.core.types import Request
from lback.core.response import Response



logger = logging.getLogger(__name__)


CSRF_TOKEN_KEY = "_csrf_token"
CSRF_FORM_FIELD_NAME = "csrfmiddlewaretoken"
CSRF_HEADER_NAME = "X-CSRF-Token"


class CSRFMiddleware(BaseMiddleware):
    """
    Middleware to protect against Cross-Site Request Forgery (CSRF) attacks.
    Generates a CSRF token and adds it to the session and request context for GET requests.
    Checks the CSRF token for POST requests (or other methods that change state).
    Returns a Forbidden response if validation fails.
    """
    def __init__(self, session_manager: SessionManager):
        """
        Initialize the CSRF middleware.
        Args:
            session_manager: Instance of the session manager to manage sessions and CSRF tokens.
             Note: While we store/retrieve token via UserSession, SessionManager
             might be needed for other potential CSRF related session operations
             or if UserSession doesn't handle underlying session data persistence.
        """
        self.session_manager = session_manager
        logger.info("CSRFMiddleware initialized.")
    def process_request(self, request: Request) -> Optional[Response]:
        """
        Processes the incoming request.
        For methods that require CSRF protection (e.g., POST, PUT, DELETE),
        validates the CSRF token. For safe methods (e.g., GET, HEAD, OPTIONS),
        ensures a CSRF token exists in the session and makes it available in context.
        Args:
            request: The incoming Request object.
        Returns:
            None if processing should continue, or a Response object
            (e.g., ForbiddenResponse) to short-circuit the request.
        """

        session: Optional[AppSession] = request.get_context('session')

        if session is None or not hasattr(session, 'get') or not hasattr(session, '__setitem__'):
            logger.error("CSRFMiddleware requires a usable Session object with 'get' and '__setitem__' methods in the request context. Ensure SessionMiddleware runs before CSRFMiddleware.")
            return Response(body=b"Internal Server Error: Session not available for CSRF.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value)
        
        csrf_token = session.get(CSRF_TOKEN_KEY) 
        request.set_context(csrf_token=csrf_token) 

        unsafe_methods = ['POST', 'PUT', 'DELETE', 'PATCH']
        safe_methods = ['GET', 'HEAD', 'OPTIONS']

        if request.method.value in unsafe_methods:

            submitted_token = None
            if isinstance(request.parsed_body, dict):
                submitted_token = request.parsed_body.get(CSRF_FORM_FIELD_NAME)

            if submitted_token is None:
                submitted_token = request.headers.get(CSRF_HEADER_NAME)
    
            expected_token = session.get(CSRF_TOKEN_KEY)

            if not (submitted_token and expected_token and secrets.compare_digest(str(submitted_token), str(expected_token))):

                if session: session.set_flash("CSRF token validation failed.", "danger")
                return Response(body=b"Forbidden: CSRF token validation failed.", status_code=HTTPStatus.FORBIDDEN.value)
            else:
                logger.debug("CSRF token validation successful.")
        if request.method.value in safe_methods and session.get(CSRF_TOKEN_KEY) is None:
            logger.info(f"CSRFMiddleware: No CSRF token found in session {getattr(session, 'session_id', 'N/A')} via get. Generating and storing a new one.")
            try:
                new_token = secrets.token_hex(16) 
                if new_token:

                    session[CSRF_TOKEN_KEY] = new_token 
                    request.set_context(csrf_token=new_token) 

                    verified_token = session.get(CSRF_TOKEN_KEY) 

                else:
                    logger.error(f"CSRFMiddleware: Failed to generate token string for session {getattr(session, 'session_id', 'N/A')} (secrets.token_hex returned None).")
            except Exception as e:
                logger.exception(f"CSRFMiddleware: Exception while generating/storing CSRF token for session {getattr(session, 'session_id', 'N/A')}: {e}")
        return None
    def process_response(self, request: Request, response: Response) -> Response:
        """
        Processes the outgoing response.
        (CSRFMiddleware typically doesn't need to modify the response in the standard flow,
         as the token is handled in process_request and template context).
        However, some implementations might add the token to a response header for JS frameworks.
        """

        csrf_token = request.get_context('csrf_token')
        safe_methods = ['GET', 'HEAD', 'OPTIONS']
        if csrf_token and request.method.value in safe_methods:
            if CSRF_HEADER_NAME not in response.headers:
                response.headers[CSRF_HEADER_NAME] = str(csrf_token)
                logger.debug(f"Added {CSRF_HEADER_NAME} header to response for {request.method.value} {request.path}.")
            else:
                logger.debug(f"{CSRF_HEADER_NAME} header already exists in response for {request.method.value} {request.path}. Skipping.")
        return response