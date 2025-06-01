import logging
from typing import Optional, Any
from sqlalchemy.orm import Session

from lback.utils.admin_user_manager import AdminUserManager
from lback.utils.session_manager import SessionManager
from lback.utils.app_session import AppSession
from lback.core.signals import dispatcher
from lback.auth.session_auth import SessionAuth
from lback.core.types import Request


logger = logging.getLogger(__name__)

class AdminAuth:
    """
    Handles authentication and authorization logic specifically for Admin Users.
    Acts as a bridge between AdminUserManager, SessionManager, and the Auth utilities.
    Integrates SignalDispatcher to emit events related to admin authentication and authorization.
    """
    def __init__(self, admin_user_manager: AdminUserManager, session_manager: SessionManager):
        """
        Initialize AdminAuth with necessary managers.
        Emits 'admin_auth_initialized' signal.

        Args:
            admin_user_manager (AdminUserManager): Instance of AdminUserManager.
            session_manager (SessionManager): Instance of SessionManager for managing sessions.
        """
        if not isinstance(admin_user_manager, AdminUserManager):
             logger.error("AdminAuth initialized without a valid AdminUserManager instance.")
             raise TypeError("admin_user_manager must be an instance of AdminUserManager.")

        if not isinstance(session_manager, SessionManager):
             logger.error("AdminAuth initialized without a valid SessionManager instance.")
             raise TypeError("session_manager must be an instance of SessionManager.")

        self.admin_user_manager = admin_user_manager
        self.session_manager = session_manager
        self.session_auth_utility = SessionAuth(session_manager=self.session_manager)

        logger.info("AdminAuth initialized.")

        if dispatcher:
            dispatcher.send("admin_auth_initialized", sender=self)
            logger.debug("Signal 'admin_auth_initialized' sent.")
        else:
            logger.warning("Dispatcher is None. Cannot send 'admin_auth_initialized' signal.")


    def register(self, db_session: Session, username: str, email: str, password: str) -> bool:
        """
        Registers a new admin user.
        Emits 'admin_registration_attempt', 'admin_registration_successful',
        or 'admin_registration_failed' signals.

        Args:
            db_session: The database session.
            username: The username for the new admin.
            email: The email for the new admin.
            password: The plain text password for the new admin.

        Returns:
            True if registration is successful, False otherwise.
        """
        logger.info(f"AdminAuth: Attempting to register admin user: '{username}'.")

        if dispatcher:
            dispatcher.send("admin_registration_attempt", sender=self, username=username, email=email)
            logger.debug(f"Signal 'admin_registration_attempt' sent for admin '{username}'.")
        else:
            logger.warning("Dispatcher is None. Cannot send 'admin_registration_attempt' signal.")
        try:
            admin_user = self.admin_user_manager.register_admin(db_session, username, email, password)
            if admin_user:
                 logger.info(f"Admin user '{username}' registered successfully (staged).")
                 if dispatcher:
                     dispatcher.send("admin_registration_successful", sender=self, admin_user=admin_user, username=username, email=email, db_session=db_session)
                     logger.debug(f"Signal 'admin_registration_successful' sent for admin '{username}'.")
                 else:
                     logger.warning("Dispatcher is None. Cannot send 'admin_registration_successful' signal.")
                 return True
            else:
                 logger.error(f"AdminUserManager failed to register admin user '{username}' without raising an exception.")

                 if dispatcher:
                     dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, error_type="manager_returned_none")
                     logger.debug(f"Signal 'admin_registration_failed' (manager_returned_none) sent for admin '{username}'.")
                 else:
                     logger.warning("Dispatcher is None. Cannot send 'admin_registration_failed' signal.")
                 return False
        except ValueError as e:
            logger.error(f"AdminAuth: Registration failed for admin user '{username}' due to validation error: {e}")
            if db_session: db_session.rollback()
            return False
        except Exception as e:
             logger.exception(f"AdminAuth: An unexpected error occurred during registration for admin user '{username}'.")
             if db_session: db_session.rollback()
             return False

    def login(self, request: Request, db_session: Session, username: str, password: str) -> Optional[Any]:
        """
        Authenticates an admin user and logs them in using session authentication.
        Emits 'admin_login_attempt', 'admin_login_successful', or 'admin_login_failed' signals.

        Args:
            request: The incoming request object.
            db_session: The database session.
            username: The username for login.
            password: The plain text password for login.

        Returns:
            The authenticated AdminUser object if successful, otherwise None.
        """
        logger.info(f"AdminAuth: Attempting login for admin user: '{username}'.")

        if dispatcher:
            dispatcher.send("admin_login_attempt", sender=self, username=username, request=request)
            logger.debug(f"Signal 'admin_login_attempt' sent for admin '{username}'.")
        else:
            logger.warning("Dispatcher is None. Cannot send 'admin_login_attempt' signal.")
        try:
            admin_user = self.admin_user_manager.authenticate_admin(db_session, username, password)
            if admin_user:
                 self.session_auth_utility.login(request, admin_user.id, user_type="admin")
                 logger.info(f"Admin user '{username}' logged in successfully.")
                 if dispatcher: 
                     dispatcher.send("admin_login_successful", sender=self, admin_user=admin_user, username=username, request=request)
                     logger.debug(f"Signal 'admin_login_successful' sent for admin '{username}'.")
                 else:
                     logger.warning("Dispatcher is None. Cannot send 'admin_login_successful' signal.")
                 return admin_user
            else:
                 logger.warning(f"AdminAuth: Failed login attempt for admin user '{username}'. Invalid credentials or inactive user.")
                 if dispatcher:
                     dispatcher.send("admin_login_failed", sender=self, username=username, request=request, reason="authentication_failed")
                     logger.debug(f"Signal 'admin_login_failed' (authentication_failed) sent for admin '{username}'.")
                 else:
                     logger.warning("Dispatcher is None. Cannot send 'admin_login_failed' signal.")
                 return None
        except Exception as e:
            logger.exception(f"AdminAuth: An unexpected error occurred during login for admin user '{username}'.")

            if db_session: db_session.rollback() 
            if dispatcher:
                dispatcher.send("admin_login_failed", sender=self, username=username, request=request, reason="exception", exception=e)
                logger.debug(f"Signal 'admin_login_failed' (exception) sent for admin '{username}'.")
            else:
                logger.warning("Dispatcher is None. Cannot send 'admin_login_failed' signal.")
            return None

    def logout(self, request: Request) -> bool:
        """
        Logs out the current admin user by ending their session.
        Emits 'admin_logout_attempt' and 'admin_logout_successful' signals.

        Args:
            request: The incoming request object. Assumes request.session is a valid AppSession instance.

        Returns:
            True if logout process was attempted (session object provided), False otherwise.
            Note: The actual session deletion is handled by AppSession.delete().
        """
        logger.info("AdminAuth: Attempting admin user logout.")

        user_session: Optional[AppSession] = request.session
        session_id = getattr(user_session, 'session_id', 'N/A')
        user_id = None
        if user_session:
             user_id = user_session.get('user_id')

        if dispatcher:
            dispatcher.send("admin_logout_attempt", sender=self, user_session=user_session, session_id=session_id, user_id=user_id)
            logger.debug(f"Signal 'admin_logout_attempt' sent for session ID '{session_id}'.")
        else:
            logger.warning("Dispatcher is None. Cannot send 'admin_logout_attempt' signal.")

        if user_session:
             try:
                 user_session.delete()
                 logger.info(f"Admin user session {session_id} ended.")
                 if dispatcher:
                     dispatcher.send("admin_logout_successful", sender=self, session_id=session_id, user_id=user_id)
                     logger.debug(f"Signal 'admin_logout_successful' sent for session ID '{session_id}'.")
                 else:
                     logger.warning("Dispatcher is None. Cannot send 'admin_logout_successful' signal.")
                 return True
             except Exception as e:
                 logger.exception(f"AdminAuth: An error occurred during session deletion for session ID {session_id}.")
                 return False
        else:
            logger.warning("AdminAuth: Logout called with no AppSession object available on request.")
            return False

    def is_admin_logged_in(self, request: Request) -> bool:
        """
        Checks if an admin user is currently logged in via session.
        Emits 'admin_authentication_check' signal, with outcome.

        Args:
            request: The incoming request object. Assumes request.session is a valid AppSession instance.

        Returns:
            True if a user ID is found in the session and is marked as admin, False otherwise.
        """
        logger.debug("AdminAuth: Checking if admin user is logged in.")
        is_admin = False
        reason = "default_false"

        try:
            is_authenticated_session = self.session_auth_utility.is_authenticated(request)
            if is_authenticated_session:
                 user_session_instance: Optional[AppSession] = request.session
                 if user_session_instance: 
                     user_type = user_session_instance.get("user_type")
                     is_admin = user_type == 'admin'
                     logger.debug(f"Session authenticated. User type in session: '{user_type}'. Is admin: {is_admin}")
                     reason = "authenticated_session_is_admin" if is_admin else "authenticated_session_not_admin"
                 else:
                     logger.error("AdminAuth: SessionAuth reported authenticated, but request.session is None.")
                     reason = "session_auth_true_but_session_none"
            else:
                 logger.debug("AdminAuth: Session authentication check failed. Admin is not logged in via session.")
                 reason = "session_authentication_failed"

        except Exception as e:
            logger.exception("AdminAuth: An unexpected error occurred while checking admin login status.")
            reason = "exception"

        if dispatcher:
            dispatcher.send("admin_authentication_check", sender=self, request=request, is_admin=is_admin, reason=reason)
            logger.debug(f"Signal 'admin_authentication_check' sent. Is admin: {is_admin}, Reason: {reason}.")
        else:
            logger.warning("Dispatcher is None. Cannot send 'admin_authentication_check' signal.")

        return is_admin
