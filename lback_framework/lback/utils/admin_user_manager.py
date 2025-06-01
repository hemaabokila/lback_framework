import logging
import re
from functools import wraps
from typing import Optional , List,Dict , Any , Callable
from sqlalchemy.orm import Session
from http import HTTPStatus

from lback.core.signals import dispatcher
from lback.auth.password_hashing import PasswordHasher
from lback.repositories.admin_user_repository import AdminUserRepository
from lback.repositories.role_repository import RoleRepository
from lback.models.adminuser import AdminUser
from lback.core.response import Response
from lback.core.types import Request


logger = logging.getLogger(__name__)

class AdminUserManager:
    """
    Service layer for Admin User related business logic.
    Manages workflows like registration and authentication.
    Receives the request-scoped database session per method call
    and instantiates Repositories with that session.
    Integrates SignalDispatcher to emit events related to admin user management.
    """

    def __init__(self):
        """
        Initializes the AdminUserManager. Repositories are instantiated per method call
        with the request-scoped database session provided to that method.
        """
        pass


    def register_admin(self, session: Session, username: str, email: str, password: str, role_name: Optional[str] = None) -> Optional[AdminUser]:
        """
        Registers a new admin user.
        Handles validation and password hashing before creating via repository.
        Receives the request-scoped database session.
        Emits 'admin_registration_started', 'admin_pre_register', 'admin_registered', or 'admin_registration_failed' signals.

        Args:
            session: The SQLAlchemy Session for database operations.
            username: The username for the new admin.
            email: The email for the new admin.
            password: The plain text password for the new admin.
            role_name: Optional name of the role to assign to the admin user.

        Returns:
            The newly created AdminUser object (added to session, but not committed) if successful, otherwise None.

        Raises:
            ValueError: If input data is invalid (missing fields, invalid email, username/email exists, role not found).
            RuntimeError: If password hashing fails.
            Exception: For other unexpected errors during database interaction.
        """
        logger.info(f"Attempting to register admin user: {username}")


        dispatcher.send("admin_registration_started", sender=self, username=username, email=email, role_name=role_name)
        logger.debug(f"Signal 'admin_registration_started' sent for admin '{username}'.")

        admin_user_repo = AdminUserRepository(session=session)
        role_repo = RoleRepository(session=session)

        try:
            if not username or not email or not password:
                 logger.warning("Attempted to register admin with missing fields.")
                 dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="validation_error", error_message="Missing required fields")
                 logger.debug("Signal 'admin_registration_failed' (validation_error) sent.")
                 raise ValueError("Username, Email, and Password are required.")
            
            if not self._validate_email(email):
                 logger.warning(f"Invalid email format: {email}")
                 dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="validation_error", error_message="Invalid email format")
                 logger.debug("Signal 'admin_registration_failed' (validation_error) sent.")
                 raise ValueError("Invalid email format.")

            if admin_user_repo.get_by_username(username):
                 logger.warning(f"Admin user registration failed. Username already exists: {username}")
                 dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="validation_error", error_message="Username already exists")
                 logger.debug("Signal 'admin_registration_failed' (validation_error) sent.")
                 raise ValueError("Admin Username already exists.")

            if admin_user_repo.get_by_email(email):
                 logger.warning(f"Admin user registration failed. Email already exists: {email}")
                 dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="validation_error", error_message="Email already exists")
                 logger.debug("Signal 'admin_registration_failed' (validation_error) sent.")
                 raise ValueError("Admin Email already exists.")

            dispatcher.send("admin_pre_register", sender=self, username=username, email=email, role_name=role_name)
            logger.debug(f"Signal 'admin_pre_register' sent for admin '{username}'.")

            try:
                hashed_password = PasswordHasher.hash_password(password)
                logger.debug("Password hashed successfully for registration.")

            except Exception as e:
                logger.error(f"Failed to hash password during registration: {e}", exc_info=True)
                dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="password_hashing_error", exception=e)
                logger.debug("Signal 'admin_registration_failed' (password_hashing_error) sent.")
                raise RuntimeError("Failed to process password.") from e

            admin_user_data: Dict[str, Any] = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "is_superuser": False,
                "is_active": True
            }

            role = None
            if role_name:
                role = role_repo.get_by_name(role_name)
                if not role:
                     logger.error(f"Role not found during admin registration: {role_name}")
                     dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="role_not_found")
                     logger.debug("Signal 'admin_registration_failed' (role_not_found) sent.")
                     raise ValueError(f"Role '{role_name}' not found.")
                admin_user_data["role"] = role

            admin_user = admin_user_repo.create(**admin_user_data)
            logger.info(f"Admin user '{username}' prepared for registration.")

            dispatcher.send("admin_registered", sender=self, admin_user=admin_user, session=session)
            logger.debug(f"Signal 'admin_registered' sent for admin '{username}'.")

            return admin_user

        except ValueError as e:
             raise e
        except RuntimeError as e:
             raise e
        except Exception as e:
             logger.exception(f"Error during admin user creation via repository for '{username}': {e}")
             dispatcher.send("admin_registration_failed", sender=self, username=username, email=email, role_name=role_name, error_type="unexpected_exception", exception=e)
             logger.debug("Signal 'admin_registration_failed' (unexpected_exception) sent.")
             raise


    def authenticate_admin(self, session: Session, username: str, password: str) -> Optional[AdminUser]:
        """
        Authenticates an admin user by username and password.
        Verifies the plain text password against the stored hash using PasswordHasher.
        Receives the request-scoped database session.
        Emits 'admin_authentication_started', 'admin_authenticated', or 'admin_authentication_failed' signals.

        Args:
            session: The SQLAlchemy Session for database operations.
            username: The username to authenticate.
            password: The plain text password.

        Returns:
            The AdminUser object if authentication is successful and user is active, otherwise None.
        """
        logger.info(f"Attempting to authenticate admin user: {username}")
        dispatcher.send("admin_authentication_started", sender=self, username=username)
        logger.debug(f"Signal 'admin_authentication_started' sent for admin '{username}'.")

        try:
            admin_user_repo = AdminUserRepository(session=session)
            admin_user = admin_user_repo.get_by_username(username)

            if admin_user and admin_user.password:
                 if PasswordHasher.verify_password(password, admin_user.password):
                     if getattr(admin_user, 'is_active', True):
                         logger.info(f"Admin user '{username}' authenticated successfully.")
                         dispatcher.send("admin_authenticated", sender=self, admin_user=admin_user, session=session)
                         logger.debug(f"Signal 'admin_authenticated' sent for admin '{username}'.")
                         return admin_user
                     else:
                         logger.warning(f"Authentication failed for admin user '{username}': User is inactive.")
                         dispatcher.send("admin_authentication_failed", sender=self, username=username, reason="user_inactive", admin_user=admin_user)
                         logger.debug(f"Signal 'admin_authentication_failed' (user_inactive) sent for admin '{username}'.")
                         return None
                 else:
                     logger.warning(f"Authentication failed for admin user '{username}': Incorrect password.")
                     dispatcher.send("admin_authentication_failed", sender=self, username=username, reason="incorrect_password", admin_user=admin_user)
                     logger.debug(f"Signal 'admin_authentication_failed' (incorrect_password) sent for admin '{username}'.")
                     return None
            else:
                logger.warning(f"Authentication failed: Admin user '{username}' not found or password not set.")
                dispatcher.send("admin_authentication_failed", sender=self, username=username, reason="user_not_found")
                logger.debug(f"Signal 'admin_authentication_failed' (user_not_found) sent for admin '{username}'.")
                return None

        except Exception as e:
            logger.exception(f"Error during authentication for admin user '{username}': {e}")
            dispatcher.send("admin_authentication_failed", sender=self, username=username, reason="unexpected_exception", exception=e)
            logger.debug(f"Signal 'admin_authentication_failed' (unexpected_exception) sent for admin '{username}'.")
            return None


    def get_admin_by_id(self, session: Session, admin_id: int) -> Optional[AdminUser]:
        """
        Get an admin user by ID using the repository.
        Receives the request-scoped database session.
        # Consider adding signals if needed, e.g., 'admin_fetched_by_id', 'admin_not_found_by_id'
        """
        logger.debug(f"Fetching admin user by ID: {admin_id}")
        admin_user_repo = AdminUserRepository(session=session)
        admin_user = admin_user_repo.get_by_id(admin_id)
        return admin_user

    def get_admin_by_username(self, session: Session, username: str) -> Optional[AdminUser]:
        """
        Get an admin user by username using the repository.
        Receives the request-scoped database session.
        # Consider adding signals if needed, e.g., 'admin_fetched_by_username', 'admin_not_found_by_username'
        """
        logger.debug(f"Fetching admin user by username: {username}")
        admin_user_repo = AdminUserRepository(session=session)
        admin_user = admin_user_repo.get_by_username(username)
        return admin_user

    def get_all_admins(self, session: Session) -> List[AdminUser]:
        """
        Get all admin users using the repository.
        Receives the request-scoped database session.
        # Consider adding signals if needed, e.g., 'all_admins_fetched'
        """
        logger.debug("Fetching all admin users.")
        admin_user_repo = AdminUserRepository(session=session)
        admins = admin_user_repo.list_all()
        return admins

    @staticmethod
    def has_permission(admin_user: Optional[AdminUser], permission_name: str) -> bool:
        """
        Check if the admin user has a specific permission.
        This is a static method as it operates on the user object, not the manager instance.
        Permission check signals are typically handled by the PermissionRequired decorator.
        """
        if not admin_user:
             logger.debug(f"Permission check failed: User is None for permission '{permission_name}'.")
             return False

        if getattr(admin_user, 'is_superuser', False):
             logger.debug(f"Permission check passed: User '{getattr(admin_user, 'username', 'N/A')}' is superuser.")
             return True

        if admin_user.role and hasattr(admin_user.role, 'permissions') and isinstance(admin_user.role.permissions, (list, set)):
             user_role_permissions = set(perm.name for perm in admin_user.role.permissions if hasattr(perm, 'name'))
             has_perm = permission_name in user_role_permissions
             logger.debug(f"Permission check for user '{getattr(admin_user, 'username', 'N/A')}' ('{permission_name}'): {has_perm}. User Role Permissions: {list(user_role_permissions)}")
             return has_perm
        else:
             logger.debug(f"Permission check failed: User '{getattr(admin_user, 'username', 'N/A')}' has no role or role has no valid permissions list for permission '{permission_name}'.")

        return False

    def permission_required(permission: str) -> Callable:
        """
        Decorator to check if the authenticated user has a specific permission.
        Assumes the authenticated user object is available on request.user.
        Uses the static has_permission method.
        Permission check signals are handled by the PermissionRequired decorator logic itself.
        """
        def decorator(func: Callable) -> Callable:
             @wraps(func)
             def wrapper(request: Request, *args, **kwargs) -> Response:
                 user = getattr(request, "user", None)
                 if not user or not AdminUserManager.has_permission(user, permission):
                      logger.warning(f"Permission denied for user {getattr(user, 'username', 'N/A')} trying to access resource requiring '{permission}'")
                      
                      return Response(
                          body=b"Permission Denied",
                          status_code=HTTPStatus.FORBIDDEN.value,
                          headers={'Content-Type': 'text/plain; charset=utf-8'}
                      )
                 return func(request, *args, **kwargs)
             return wrapper
        return decorator

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format."""
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.fullmatch(regex, email) is not None
