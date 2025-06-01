import logging
from typing import Optional, Union
from uuid import UUID
from datetime import datetime

from lback.utils.session_manager import SessionManager
from lback.utils.app_session import AppSession
from lback.core.types import Request
from lback.core.signals import dispatcher


logger = logging.getLogger(__name__)

class SessionAuth:
    """
    Utility class for handling session-based authentication.
    Manages setting and getting user IDs and user types in the session data.
    Requires a SessionManager instance to interact with session storage.
    """
    def __init__(self, session_manager: SessionManager):
        """
        Initialize SessionAuth with a SessionManager instance.
        Args:
            session_manager (SessionManager): The SessionManager instance.
        """
        if not isinstance(session_manager, SessionManager):
            logger.error("SessionAuth initialized without a valid SessionManager instance.")
            raise TypeError("session_manager must be an instance of SessionManager.")
        self.session_manager = session_manager
        logger.info("SessionAuth utility initialized.")

    def login(self, request: Request, user_id: Union[int, str, UUID], user_type: str = "user") -> bool:
        """
        Logs a user in by setting their ID and type in the session data.
        Assumes SessionMiddleware has run and populated request.session.
        Args:
            request: The Request object, expected to have a 'session' attribute (AppSession instance).
            user_id: The ID of the user to log in.
            user_type: The type of the user ('user' or 'admin').

        Returns:
            True if the user ID was successfully set in an active session, False otherwise.
        """
        logger.info(f"SessionAuth.login: Attempting to log in user ID: {user_id}, type: {user_type}.")

        user_session: Optional[AppSession] = getattr(request, 'session', None)

        if user_session is not None:
            logger.debug(f"SessionAuth.login: Type of request.session: {type(user_session)}")

        is_session_active = False
        if user_session is not None and isinstance(user_session, AppSession) and user_session.expires_at is not None:
             is_session_active = datetime.utcnow() < user_session.expires_at
             logger.debug(f"SessionAuth.login: Session {user_session.session_id} expires at {user_session.expires_at}. Current UTC is {datetime.utcnow()}. Is active: {is_session_active}")

        elif user_session is not None and isinstance(user_session, AppSession) and user_session.expires_at is None:
             logger.warning(f"SessionAuth.login: Session {user_session.session_id} has expires_at=None. Not considered active for login.")
             is_session_active = False

        if user_session is not None and isinstance(user_session, AppSession) and is_session_active:
            logger.debug(f"SessionAuth.login: request.session is not None, is AppSession, and is active. Proceeding with login.")

            try:
                user_session['user_id'] = user_id
                user_session['user_type'] = user_type
                logger.debug(f"SessionAuth.login: User ID {user_id} and type {user_type} set in session {user_session.session_id}.")

                if dispatcher:
                    dispatcher.send("user_logged_in", sender=self, request=request, user_id=user_id, user_type=user_type, session=user_session)
                    logger.debug(f"Signal 'user_logged_in' sent for user ID {user_id}.")
                else:
                    logger.warning("Dispatcher is None. Cannot send 'user_logged_in' signal.")

                logger.info(f"SessionAuth.login: User ID {user_id} successfully logged in via session {user_session.session_id}.")
                return True
            
            except Exception as e:
                 logger.exception(f"SessionAuth.login: Error setting user data on AppSession for user ID {user_id}: {e}")
                 return False

        else:
            logger.error(f"SessionAuth.login: Attempted to log in user ID {user_id}, but request.session is None, not a valid session object, or is inactive.")

            if dispatcher:
                reason = "session_unavailable" if user_session is None else ("invalid_session_object" if not isinstance(user_session, AppSession) else ("session_inactive" if user_session.expires_at is not None else "session_expiry_missing"))
                dispatcher.send("session_login_failed", sender=self, request=request, user_id=user_id, user_type=user_type, reason=reason)
                logger.debug(f"Signal 'session_login_failed' ({reason}) sent for user ID {user_id}.")
                
            else:
                logger.warning("Dispatcher is None. Cannot send 'session_login_failed' signal.")

            return False

    def is_authenticated(self, request: Request) -> bool:
        """
        Checks if a user is authenticated based on session data.
        Args:
            request: The Request object, expected to have a 'session' attribute (AppSession instance).
        Returns:
            True if a user ID is found in the session data AND the session is active, False otherwise.
        """

        user_session: Optional[AppSession] = getattr(request, 'session', None)

        if user_session is not None:
            logger.debug(f"SessionAuth.is_authenticated: Type of request.session: {type(user_session)}")


        is_authenticated_status = False
        user_id = None
        reason = "default_false"

        if user_session is not None and isinstance(user_session, AppSession):
            is_session_active = user_session.expires_at is not None and datetime.utcnow() < user_session.expires_at
            logger.debug(f"SessionAuth.is_authenticated: Session {user_session.session_id} active check (using expires_at {user_session.expires_at}): {is_session_active}")

            if is_session_active:
                user_id = user_session.get('user_id')
                if user_id is not None:
                    is_authenticated_status = True
                    reason = "authenticated_and_active"
                    logger.debug(f"SessionAuth.is_authenticated: User ID {user_id} found in active session {user_session.session_id}. Authenticated.")
                else:
                    reason = "active_but_no_user_id"
                    logger.debug(f"SessionAuth.is_authenticated: Active session {user_session.session_id} found, but no user ID in data.")
            else:
                reason = "session_inactive" if user_session.expires_at is not None else "session_expiry_missing"
                logger.debug(f"SessionAuth.is_authenticated: Session {user_session.session_id} found but is inactive or expiry missing.")
        else:
            reason = "session_unavailable"
            logger.debug("SessionAuth.is_authenticated: request.session is None or not AppSession.")


        if dispatcher:
            dispatcher.send("session_authentication_check", sender=self, request=request, user_id=user_id, is_authenticated=is_authenticated_status, reason=reason)
            logger.debug(f"Signal 'session_authentication_check' sent. Is authenticated: {is_authenticated_status}, Reason: {reason}.")
        else:
            logger.warning("Dispatcher is None. Cannot send 'session_authentication_check' signal.")

        return is_authenticated_status


    def get_current_user_id(self, request: Request) -> Optional[Union[int, str, UUID]]:
        """
        Retrieves the authenticated user's ID from the session data, ONLY if the session is active.
        Args:
            request: The Request object, expected to have a 'session' attribute (AppSession instance).
        Returns:
            The user ID if authenticated and session is active, otherwise None.
        """
        logger.debug("SessionAuth.get_current_user_id: Attempting to get current user ID from session.")
        user_session: Optional[AppSession] = getattr(request, 'session', None)

        if user_session is not None and isinstance(user_session, AppSession):
             is_session_active = user_session.expires_at is not None and datetime.utcnow() < user_session.expires_at
             logger.debug(f"SessionAuth.get_current_user_id: Session {user_session.session_id} active check (using expires_at {user_session.expires_at}): {is_session_active}")

             if is_session_active:
                user_id = user_session.get('user_id')
                logger.debug(f"SessionAuth.get_current_user_id: User ID found in active session data: {user_id}")
                return user_id
             else:
                 logger.debug(f"SessionAuth.get_current_user_id: Session {user_session.session_id} found but is inactive or expiry missing. Cannot get user ID.")
                 return None
        else:
            logger.debug("SessionAuth.get_current_user_id: request.session is None or not AppSession. Cannot get user ID.")
            return None

    def logout(self, request: Request) -> bool:
        """
        Logs out the current user by deleting their session.
        Args:
            request: The Request object, expected to have a 'session' attribute (AppSession instance).
        Returns:
            True if a session object was available to attempt deletion, False otherwise.
        """
        logger.info("SessionAuth.logout: Attempting user logout by deleting session.")
        user_session: Optional[AppSession] = getattr(request, 'session', None)
        if user_session is not None and isinstance(user_session, AppSession):
            session_id = user_session.session_id if user_session.session_id else 'N/A'
            user_id = user_session.get('user_id')

            try:
                user_session.delete()
                logger.info(f"SessionAuth.logout: Session {session_id} deleted for user ID {user_id}.")

                if dispatcher:
                    dispatcher.send("user_logged_out", sender=self, request=request, session_id=session_id, user_id=user_id)
                    logger.debug(f"Signal 'user_logged_out' sent for session ID {session_id}.")

                else:
                    logger.warning("Dispatcher is None. Cannot send 'user_logged_out' signal.")
                return True
            
            except Exception as e:
                 logger.exception(f"SessionAuth.logout: Error deleting session {session_id}: {e}")
                 return False
        else:
            logger.warning("SessionAuth.logout: request.session is None or not AppSession. Cannot perform logout.")
            return False
