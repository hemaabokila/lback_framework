import logging
from http import HTTPStatus
from typing import Optional, Any
from sqlalchemy.orm import Session

from lback.core.base_middleware import BaseMiddleware
from lback.core.response import Response
from lback.utils.app_session import AppSession
from lback.utils.admin_user_manager import AdminUserManager
from lback.utils.user_manager import UserManager
from lback.auth.jwt_auth import JWTAuth
from lback.core.types import Request


logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """
    Middleware to handle user authentication based on either session data or Authorization header (Bearer token).
    It attempts session authentication first (by checking data in request.session). If not found/valid, it attempts token authentication.
    Attaches the authenticated user (User or AdminUser) to request.user.
    Relies on SessionMiddleware to attach the session object to request.session for ALL requests.
    Requires SQLAlchemyMiddleware to run before it to provide the DB session.
    Requires the router/handler to set request.route_requires_auth for protected routes.
    """
    def __init__(self, admin_user_manager: AdminUserManager, user_manager: UserManager, jwt_auth: JWTAuth):
        """
        Initializes AuthMiddleware with necessary managers and auth utilities.
        These dependencies should be initialized once globally (e.g., in core/server.py).
        Args:
            admin_user_manager: The AdminUserManager instance.
            user_manager: The UserManager instance for regular users.
            jwt_auth_utility: The JWTAuth instance from auth.jwt_auth.
        """
        if not isinstance(admin_user_manager, AdminUserManager):
            logger.error("AuthMiddleware initialized without a valid AdminUserManager instance.")
        if not isinstance(user_manager, UserManager):
            logger.error("AuthMiddleware initialized without a valid UserManager instance.")
        if not isinstance(jwt_auth, JWTAuth):
            logger.error("AuthMiddleware initialized without a valid JWTAuth instance.")
        self.admin_user_manager = admin_user_manager
        self.user_manager = user_manager
        self.jwt_auth_utility = jwt_auth
        logger.info("AuthMiddleware initialized for Session and Token authentication.")

    def process_request(self, request: Request):
        """
        Processes the incoming request to authenticate the user via session data or token.
        Relies on request.session being populated by SessionMiddleware.
        Attaches request.user (User or AdminUser) if authenticated.
        Returns a Response if authentication/authorization fails AND the route requires auth, otherwise returns None.
        """

        db_session: Optional[Session] = request.get_context('db_session')
        request_session_wrapper: Optional[AppSession] = request.get_context('session')

        if not db_session:
            logger.error("AuthMiddleware: Database session not found on request context. Ensure SQLAlchemyMiddleware runs before AuthMiddleware.")
            return Response(body=b"Internal Server Error: Database session not available for authentication.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
        if request_session_wrapper is None:
            logger.error("AuthMiddleware: Session object not found on request context. Ensure SessionMiddleware runs before AuthMiddleware.")
            return Response(body=b"Internal Server Error: Session not available.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
        
        authenticated_user: Optional[Any] = None

        user_id_from_session = request_session_wrapper.get('user_id')
        user_type_from_session = request_session_wrapper.get('user_type')

        if user_id_from_session is not None and user_type_from_session:
            try:
                if user_type_from_session == 'admin':
                    authenticated_user = self.admin_user_manager.get_admin_by_id(db_session, user_id_from_session)
 
                elif user_type_from_session == 'user':
                    if hasattr(self, 'user_manager') and self.user_manager:
                        authenticated_user = self.user_manager.get_user_by_id(db_session, user_id_from_session)
                        if authenticated_user:
                            user_groups = [group.name for group in authenticated_user.groups]
                            request_session_wrapper['user_groups'] = user_groups
                    else:
                        logger.error("AuthMiddleware: UserManager not initialized but user_type is 'user' in session.")
                        authenticated_user = None
                else:
                    logger.warning(f"AuthMiddleware: Unknown user_type '{user_type_from_session}' in session data for user ID {user_id_from_session}. Invalid user data in session.")
                    authenticated_user = None

                if authenticated_user is None:
                    logger.warning(f"AuthMiddleware: User with ID {user_id_from_session} (type: {user_type_from_session}) from session data not found or invalid in DB. User is not authenticated via session. Clearing session data.")
                    if 'user_id' in request_session_wrapper:
                        del request_session_wrapper['user_id']
                    if 'user_type' in request_session_wrapper:
                        del request_session_wrapper['user_type']
                    if 'user_groups' in request_session_wrapper:
                        del request_session_wrapper['user_groups']
  
            except Exception as e:
                logger.exception(f"AuthMiddleware: Error loading user {user_id_from_session} (type: {user_type_from_session}) from session data: {e}")
                authenticated_user = None
        else:

            if 'user_id' in request_session_wrapper:
                del request_session_wrapper['user_id']
            if 'user_type' in request_session_wrapper:
                del request_session_wrapper['user_type']
            if 'user_groups' in request_session_wrapper:
                del request_session_wrapper['user_groups']


        if authenticated_user is None:

            auth_header = request.headers.get('Authorization')
            if auth_header:
                if self.jwt_auth_utility:
                    try:
                        token_parts = auth_header.split(" ")
                        if len(token_parts) == 2 and token_parts[0].lower() == 'bearer':
                            token = token_parts[1]
                            decoded_payload = self.jwt_auth_utility.decode_token(token)
                            
                            if decoded_payload:
                                user_id = decoded_payload.get("user_id")
                                user_type_from_token = decoded_payload.get("user_type")
                                
                                if user_id is not None and user_type_from_token:
                                    try:
                                        authenticated_user_from_token = None
                                        if user_type_from_token == 'admin':
                                            authenticated_user_from_token = self.admin_user_manager.get_admin_by_id(db_session, user_id)
                                            if authenticated_user_from_token:
                                                logger.info(f"AuthMiddleware: Token authentication successful for AdminUser '{getattr(authenticated_user_from_token, 'username', 'N/A')}' ({request.method} {request.path}).")
                                        elif user_type_from_token == 'user':
                                            if hasattr(self, 'user_manager') and self.user_manager:
                                                authenticated_user_from_token = self.user_manager.get_user_by_id(db_session, user_id)
                                                if authenticated_user_from_token:
                                                    user_groups = [group.name for group in authenticated_user_from_token.groups]
                                                    logger.info(f"AuthMiddleware: Token authentication successful for Regular User '{getattr(authenticated_user_from_token, 'username', 'N/A')}' (Groups: {user_groups}).")
                                            else:
                                                logger.error("AuthMiddleware: UserManager not initialized but user_type is 'user' in token.")
                                                authenticated_user_from_token = None
                                        else:
                                            logger.warning(f"AuthMiddleware: Unknown user_type '{user_type_from_token}' in token payload for user ID {user_id}.")
                                            authenticated_user_from_token = None

                                        if authenticated_user_from_token:
                                            authenticated_user = authenticated_user_from_token
                                        else:
                                            logger.warning(f"AuthMiddleware: User with ID {user_id} (type: {user_type_from_token}) from token not found in DB.")
                                            return Response(body=b"Unauthorized: User from token not found or invalid type.", status_code=HTTPStatus.UNAUTHORIZED.value, headers={'Content-Type': 'text/plain'})
                                    except Exception as e:
                                        logger.exception(f"AuthMiddleware: Error loading user {user_id} (type: {user_type_from_token}) from token: {e}")
                                        return Response(body=b"Internal Server Error during token user loading.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
                                else:
                                    logger.debug("AuthMiddleware: JWT token payload missing user_id or user_type.")
                                    return Response(body=b"Unauthorized: Invalid token payload.", status_code=HTTPStatus.UNAUTHORIZED.value, headers={'Content-Type': 'text/plain'})
                            else:
                                logger.debug("AuthMiddleware: JWT token validation failed (decode_token returned None).")
                                return Response(body=b"Unauthorized: Invalid or expired token.", status_code=HTTPStatus.UNAUTHORIZED.value, headers={'Content-Type': 'text/plain'})
                        else:
                            logger.warning(f"AuthMiddleware: Malformed Authorization header format for {request.method} {request.path}. Expected 'Bearer <token>'.")
                            return Response(body=b"Unauthorized: Malformed Authorization header format.", status_code=HTTPStatus.UNAUTHORIZED.value, headers={'Content-Type': 'text/plain'})
                    except Exception as e:
                        logger.exception(f"AuthMiddleware: Unexpected error during token authentication for {request.method} {request.path}: {e}")
                        return Response(body=b"Internal Server Error during authentication.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
                else:
                    logger.warning("AuthMiddleware: JWT_AUTH_UTILITY not configured but Authorization header found.")
                    return Response(body=b"Internal Server Error: JWT Authentication not configured.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
            else:
                logger.debug("AuthMiddleware: No Authorization header found. Token authentication skipped.")

        logger.debug(f"AuthMiddleware: Setting request.user to: {authenticated_user}")
        request.user = authenticated_user
        
        route_requires_auth = getattr(request, 'route_requires_auth', False)
        if route_requires_auth and request.user is None:
            logger.warning(f"Authentication required but failed for protected route: {request.method} {request.path}. User is None.")
            if request_session_wrapper and hasattr(request_session_wrapper, 'set_flash') and callable(request_session_wrapper.set_flash):
                request_session_wrapper.set_flash("Authentication is required to access this resource.", "warning")
            else:
                logger.warning("AuthMiddleware: request.session or its set_flash method not available to set flash message.")
            return Response(body=b"Unauthorized: Authentication is required to access this resource.", status_code=HTTPStatus.UNAUTHORIZED.value, headers={'Content-Type': 'text/plain'})
        
        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """
        Processes the outgoing response.
        Does NOT handle session cookie writing - this is the responsibility of SessionMiddleware.
        This method just passes the response along.
        """
        logger.debug(f"AuthMiddleware processing response for {request.method} {request.path}. Passing response.")
        return response