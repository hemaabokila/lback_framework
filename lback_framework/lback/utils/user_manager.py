import logging
import re 
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from lback.auth.password_hashing import PasswordHasher
from lback.core.signals import dispatcher
from lback.repositories.user_repository import UserRepository
from lback.models.user import User, Group
from lback.utils.email_sender import EmailSender
from lback.core.config import Config

from .validation import ValidationError, PasswordValidator

logger = logging.getLogger(__name__)

class UserManager:
    """
    Service layer for User related business logic.
    Manages workflows like registration, authentication, and user management.
    Receives the request-scoped database session per method call
    and instantiates Repositories with that session.
    Integrates SignalDispatcher to emit events related to user management.
    """

    def __init__(self, email_sender: EmailSender, password_validator: PasswordValidator):
        """
        Initializes the UserManager. Repositories are instantiated per method call
        with the request-scoped database session provided to that method.
        """
        self.email_sender = email_sender
        self.password_validator = password_validator
        logger.info("UserManager initialized.")

    def register_user(self, session: Session, username: str, email: str, plain_password: str) -> Optional[User]:
        """
        Registers a new user with validation, password complexity checks,
        and initiates email verification. Assigns the user to the 'basic_user' group.
        Emits 'user_registration_started', 'user_pre_register', 'user_registered',
        'user_email_verification_initiated', or 'user_registration_failed' signals.
        """
        logger.info(f"Attempting to register user: {username}")
        dispatcher.send("user_registration_started", sender=self, username=username, email=email)
        user_repo = UserRepository(session=session)

        try:
            self._validate_registration_data(username, email, plain_password)
            
            self.password_validator.validate(plain_password)

            if user_repo.get_by_username(username):
                logger.warning(f"Registration failed. Username already exists: {username}")
                dispatcher.send("user_registration_failed", sender=self, username=username, email=email, error_type="validation_error", error_message="Username already exists")
                raise ValidationError("Username already exists.")

            if user_repo.get_by_email(email):
                logger.warning(f"Registration failed. Email already exists: {email}")
                dispatcher.send("user_registration_failed", sender=self, username=username, email=email, error_type="validation_error", error_message="Email already exists.")
                raise ValidationError("Email already exists.")

            dispatcher.send("user_pre_register", sender=self, username=username, email=email)

            try:

                user = User(
                    username=username,
                    email=email,
                    is_active=True,
                    is_email_verified=False,
                )
                user.set_password(plain_password)

                basic_user_group = session.query(Group).filter_by(name='basic_user').first()
                if not basic_user_group:
                    logger.critical("Critical Error: 'basic_user' group not found in database. Please run database seeding (e.g., 'python manage.py seed_db').")
                    raise ValueError("Default group 'basic_user' not found. Database not seeded correctly.")
                
                user.groups.append(basic_user_group)
                logger.info(f"User '{username}' assigned to 'basic_user' group.")

                session.add(user)
                session.flush()
                user.generate_email_verification_token()
                config=Config()
                allowed_hosts = getattr(config, 'ALLOWED_HOSTS', [])

                if allowed_hosts:
                    verification_host = allowed_hosts[0]
                else:

                    logger.warning("ALLOWED_HOSTS not configured or empty. Using default localhost for verification link.")
                    verification_host = "127.0.0.1:10000"
                try:
                    verification_link = f"http://{verification_host}/api/auth/verify-email/?token={user.email_verification_token}"
                    self.email_sender.send_email(
                        to_email=user.email,
                        subject="Please Verify Your Email Address",
                        body=f"Hello {user.username},\n\nPlease click the following link to verify your email address: {verification_link}"
                    )
                    logger.info(f"Verification email sent to {user.email}.")
                    dispatcher.send("user_email_verification_initiated", sender=self, user=user)
                except Exception as email_err:
                    logger.error(f"Failed to send verification email to {user.email}: {email_err}", exc_info=True)
                    dispatcher.send("user_registration_failed", sender=self, username=username, email=email, error_type="email_send_failed", exception=email_err)
                    raise RuntimeError("Failed to send verification email.") from email_err

                logger.info(f"User '{username}' registered and email verification initiated.")
                dispatcher.send("user_registered", sender=self, user=user, session=session)
                return user

            except Exception as e:
                logger.exception(f"Error during user creation/email initiation for '{username}': {e}")
                dispatcher.send("user_registration_failed", sender=self, username=username, email=email, error_type="repository_error", exception=e)
                raise

        except ValidationError as e:
            raise e
        except ValueError as e:
            logger.error(f"Registration failed due to missing default group: {e}")
            raise
        except RuntimeError as e:
            raise e
        except Exception as e:
            logger.exception(f"An unexpected error occurred during user registration for '{username}': {e}")
            dispatcher.send("user_registration_failed", sender=self, username=username, email=email, error_type="unexpected_exception", exception=e)
            raise

    @staticmethod
    def _validate_registration_data(username: str, email: str, password: str):
        """Validate user registration data (basic format checks for presence and length)."""
        if not username or not email or not password:
            raise ValidationError("Username, Email, and Password are required.")
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

    def authenticate_user(self, session: Session, username: str, password: str, require_email_verified: bool = True) -> Optional[User]:
        """
        Authenticates user login credentials, with an option to require email verification.
        Emits 'user_authentication_started', 'user_authenticated', or 'user_authentication_failed' signals.
        """
        logger.info(f"Attempting to authenticate user: {username}")
        dispatcher.send("user_authentication_started", sender=self, username=username)

        try:
            user_repo = UserRepository(session=session)
            user = user_repo.get_by_username(username)

            if not user:
                logger.warning(f"Authentication failed: User '{username}' not found.")
                dispatcher.send("user_authentication_failed", sender=self, username=username, reason="user_not_found")
                return None

            if not user.is_active:
                logger.warning(f"Authentication failed for user '{username}': User is inactive.")
                dispatcher.send("user_authentication_failed", sender=self, username=username, reason="user_inactive", user=user)
                return None

            if require_email_verified and not user.is_email_verified:
                logger.warning(f"Authentication failed for user '{username}': Email not verified.")
                dispatcher.send("user_authentication_failed", sender=self, username=username, reason="email_not_verified", user=user)
                raise ValidationError("Please verify your email address to log in.")

            if not user.password or not PasswordHasher.verify_password(password, user.password):
                logger.warning(f"Authentication failed for user '{username}': Incorrect password.")
                dispatcher.send("user_authentication_failed", sender=self, username=username, reason="incorrect_password", user=user)
                return None

            logger.info(f"User '{username}' authenticated successfully.")
            dispatcher.send("user_authenticated", sender=self, user=user, session=session)
            return user

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.exception(f"Error during authentication for user '{username}': {e}")
            dispatcher.send("user_authentication_failed", sender=self, username=username, reason="unexpected_exception", exception=e)
            return None
        
    def verify_user_email(self, session: Session, token: str) -> Optional[User]:
        """
        Verifies a user's email using the provided token.
        Emits 'user_email_verification_successful' or 'user_email_verification_failed' signals.
        """
        logger.info(f"Attempting to verify email with token: {token[:10]}...")
        user_repo = UserRepository(session=session)
        user = None
        try:
            user = user_repo.get_by_email_verification_token(token)

            if not user:
                logger.warning(f"Email verification failed: Invalid or non-existent token '{token[:10]}...'.")
                dispatcher.send("user_email_verification_failed", sender=self, token_prefix=token[:10] + "...", error_type="invalid_token")
                raise ValidationError("Invalid or expired verification link.")

            if user.is_email_verified:
                logger.info(f"Email already verified for user '{user.username}'.")
                dispatcher.send("user_email_verification_successful", sender=self, user=user, reason="already_verified")
                return user

            if user.verify_email(token):
                session.add(user)
                logger.info(f"Email verified successfully for user '{user.username}'.")
                dispatcher.send("user_email_verification_successful", sender=self, user=user)
                return user
            else:
                logger.warning(f"Email verification failed for user '{user.username}': Token expired or mismatched.")
                dispatcher.send("user_email_verification_failed", sender=self, user=user, error_type="token_mismatch_or_expired")
                raise ValidationError("Invalid or expired verification link.")

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.exception(f"Error during email verification with token '{token[:10]}...': {e}")
            dispatcher.send("user_email_verification_failed", sender=self, token_prefix=token[:10] + "...", error_type="unexpected_exception", exception=e, user=user)
            raise

    def update_user(self, session: Session, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Update an existing user's data using the repository.
        Handles password hashing, and can update email verification status.
        Note: Group membership changes should be handled explicitly, not via 'data' dict.
        """
        logger.info(f"Attempting to update user with ID: {user_id}")
        dispatcher.send("user_update_started", sender=self, user_id=user_id, update_data=data)

        user_repo = UserRepository(session=session)
        user = None

        try:
            user = user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"Update failed: User with ID {user_id} not found.")
                dispatcher.send("user_update_failed", sender=self, user_id=user_id, update_data=data, error_type="user_not_found")
                raise ValidationError("User not found.")

            if 'password' in data and data['password']:
                self.password_validator.validate(data['password'])
                try:
                    hashed_password = PasswordHasher.hash_password(data['password'])
                    data['password'] = hashed_password
                except Exception as e:
                    logger.error(f"Failed to hash new password during update: {e}", exc_info=True)
                    dispatcher.send("user_update_failed", sender=self, user_id=user_id, update_data=data, error_type="password_hashing_error", exception=e, user=user)
                    raise RuntimeError("Failed to process new password.") from e
            elif 'password' in data and not data['password']:
                del data['password']

            if 'is_email_verified' in data:
                if data['is_email_verified'] is True and not user.is_email_verified:
                    logger.info(f"User '{user.username}' email status changed to verified via update.")
                    dispatcher.send("user_email_verified", sender=self, user=user, reason="manual_update")
                elif data['is_email_verified'] is False and user.is_email_verified:
                    logger.warning(f"User '{user.username}' email status changed to unverified via update.")
            

            if 'role_name' in data:
                logger.warning(f"Attempted to update 'role_name' for user '{user.username}' via update_user. This is deprecated. Use group management methods instead.")
                del data['role_name']

            dispatcher.send("user_pre_update", sender=self, user=user, update_data=data, session=session)
            updated_user = user_repo.update(user, **data)
            logger.info(f"User '{user.username}' prepared for update.")
            dispatcher.send("user_updated", sender=self, user=updated_user, session=session)
            return updated_user
        except ValidationError as e:
            raise e
        except RuntimeError as e:
            raise e
        except Exception as e:
            logger.exception(f"Error during user update via repository for ID '{user_id}': {e}")
            error_type = "repository_error" if isinstance(e, Exception) else "unexpected_exception"
            dispatcher.send("user_update_failed", sender=self, user_id=user_id, update_data=data, error_type=error_type, exception=e, user=user)
            raise

    def delete_user(self, session: Session, user_id: int):
        """
        Delete a user using the repository.
        Receives the request-scoped database session.
        Emits 'user_deletion_started', 'user_pre_delete', 'user_deleted', or 'user_deletion_failed' signals.

        Args:
            session: The SQLAlchemy Session for database operations.
            user_id: The ID of the user to delete.

        Raises:
            ValidationError: If user is not found.
            Exception: For other unexpected errors.
        """
        logger.info(f"Attempting to delete user with ID: {user_id}")
        dispatcher.send("user_deletion_started", sender=self, user_id=user_id)
        logger.debug(f"Signal 'user_deletion_started' sent for user ID '{user_id}'.")

        user_repo = UserRepository(session=session)
        user = None

        try:
            user = user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"Deletion failed: User with ID {user_id} not found.")
                dispatcher.send("user_deletion_failed", sender=self, user_id=user_id, error_type="user_not_found")
                logger.debug(f"Signal 'user_deletion_failed' (user_not_found) sent for user ID '{user_id}'.")
                raise ValidationError("User not found.")
            dispatcher.send("user_pre_delete", sender=self, user=user, session=session)
            logger.debug(f"Signal 'user_pre_delete' sent for user '{user.username}'.")
            user_repo.delete(user)
            logger.info(f"User '{user.username}' prepared for deletion.")
            dispatcher.send("user_deleted", sender=self, user_id=user_id, username=user.username, session=session)
            logger.debug(f"Signal 'user_deleted' sent for user '{user.username}'.")

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.exception(f"Error during user deletion via repository for ID '{user_id}': {e}")
            error_type = "repository_error" if isinstance(e, Exception) else "unexpected_exception"
            user_details = {"user_id": user_id}
            if user:
                user_details["username"] = user.username
            dispatcher.send("user_deletion_failed", sender=self, **user_details, error_type=error_type, exception=e)
            logger.debug(f"Signal 'user_deletion_failed' ({error_type}) sent for user ID '{user_id}'.")
            raise


    def get_user_by_id(self, session: Session, user_id: int) -> Optional[User]:
        """
        Get a user by their ID using the repository.
        Receives the request-scoped database session.
        """
        logger.debug(f"Fetching user by ID: {user_id}")
        user_repo = UserRepository(session=session)
        user = user_repo.get_by_id(user_id)
        return user

    def get_user_by_email(self, session: Session, email: str) -> Optional[User]:
        """
        Get a user by their email address using the repository.
        Receives the request-scoped database session.
        """
        logger.debug(f"Fetching user by email: {email}")
        user_repo = UserRepository(session=session)
        user = user_repo.get_by_email(email)
        return user
    
    def get_user_by_username(self, session: Session, username: str) -> Optional[User]:
        """
        Get a user by their username using the repository.
        Receives the request-scoped database session.
        """
        logger.debug(f"Fetching user by username: {username}")
        user_repo = UserRepository(session=session)
        user = user_repo.get_by_username(username)
        return user

    def get_all_users(self, session: Session) -> List[User]:
        """
        Get all users using the repository.
        Receives the request-scoped database session.
        """
        logger.debug("Fetching all users.")
        user_repo = UserRepository(session=session)
        users = user_repo.list_all()
        return users
    
    def search_users(self, session: Session, **criteria: Any) -> List[User]:
        """
        Search for users based on provided criteria using the repository or session.
        Receives the request-scoped database session.

        Args:
            session: The SQLAlchemy Session for database operations.
            **criteria: Keyword arguments for search criteria (e.g., username="test").

        Returns:
            A list of User objects matching the criteria.
        """
        logger.debug(f"Searching users with criteria: {criteria}")
        user_repo = UserRepository(session=session)
        try:
            query = session.query(User)
            for key, value in criteria.items():
                if hasattr(User, key):
                    query = query.filter(getattr(User, key) == value)
                else:
                    logger.warning(f"Search criteria '{key}' not found on User model. Skipping.")
            return query.all()
        except Exception as e:
            logger.exception(f"Error during user search: {e}")
            return []

    def reset_password_request(self, session: Session, email: str, reset_url_path: Optional[str] = None) -> bool:
        """
        Initiates a password reset request for a user.
        Generates a reset token, stores it on the user, and prepares for email sending.

        Args:
            session: The SQLAlchemy Session.
            email: The email of the user requesting reset.
            reset_url_path: The base URL path to use for the reset link (e.g., "/reset-password-confirm/").
                            If None, it defaults to the API path.
        """
        logger.info(f"Password reset requested for '{email}'.")
        dispatcher.send("password_reset_request_started", sender=self, email=email)
        user_repo = UserRepository(session=session)

        config = Config()
        allowed_hosts = getattr(config, 'ALLOWED_HOSTS', [])
        verification_host = "127.0.0.1:10000"

        if allowed_hosts:
            verification_host = allowed_hosts[0]
        else:
            logger.warning("ALLOWED_HOSTS not configured or empty. Using default localhost for verification link.")

        final_reset_path = reset_url_path if reset_url_path else "/api/auth/reset-password/"

        try:
            user = user_repo.get_by_email(email)
            if user:
                user.auth_token = PasswordHasher.generate_random_token(length=64) 
                user.token_expiry = datetime.utcnow() + timedelta(hours=1)
                session.add(user)
                session.flush()

                reset_link = f"http://{verification_host}{final_reset_path}?token={user.auth_token}"

                self.email_sender.send_email(
                    to_email=user.email,
                    subject="Password Reset Request",
                    body=f"Hello {user.username},\n\nPlease click the following link to reset your password: {reset_link}"
                )
                logger.info(f"Password reset email sent to {user.email}.")
                dispatcher.send("password_reset_request_processed", sender=self, email=email, user=user, session=session)
                return True
            else:
                logger.warning(f"Password reset request failed: User with email '{email}' not found.")
                dispatcher.send("password_reset_request_failed", sender=self, email=email, error_type="user_not_found")
                return False
        except Exception as e:
            logger.exception(f"Error during password reset request for '{email}': {e}")
            dispatcher.send("password_reset_request_failed", sender=self, email=email, error_type="unexpected_exception", exception=e)
            raise

    def reset_password(self, session: Session, token: str, new_password: str) -> bool:
        """
        Resets a user's password using a password reset token.
        Verifies the token, updates the password, and clears the token.
        """
        logger.info(f"Password reset with token: {token[:10]}...")
        dispatcher.send("password_reset_started", sender=self, token_prefix=token[:10] + "...")
        user_repo = UserRepository(session=session)
        user = None
        try:
            self.password_validator.validate(new_password)

            user = user_repo.get_user_by_auth_token_and_expiry(token)

            if not user:
                logger.warning(f"Password reset failed: Invalid or expired token.")
                dispatcher.send("password_reset_failed", sender=self, token_prefix=token[:10] + "...", error_type="invalid_token")
                raise ValidationError("Invalid or expired reset token.")

            user.set_password(new_password)
            user.auth_token = None
            user.token_expiry = None

            session.add(user)

            logger.info(f"Password reset successful for user ID {user.id}.")
            dispatcher.send("password_reset_successful", sender=self, user=user, session=session)
            return True

        except ValidationError as e:
            raise e
        except RuntimeError as e:
            raise e
        except Exception as e:
            logger.exception(f"Error during password reset with token for token prefix '{token[:10]}...': {e}")
            error_type = "repository_error" if isinstance(e, Exception) else "unexpected_exception"
            dispatcher.send("password_reset_failed", sender=self, token_prefix=token[:10] + "...", error_type=error_type, exception=e, user=user)
            raise

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format."""
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.fullmatch(regex, email) is not None