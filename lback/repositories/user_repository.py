from sqlalchemy.orm import Session
from typing import List, Optional, Any
import logging
from datetime import datetime

from lback.core.signals import dispatcher
from lback.models.user import User

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Repository for User model data access.
    Provides methods to interact with the database for User entities.
    Requires a SQLAlchemy Session to be provided upon initialization.
    Integrates SignalDispatcher to emit events related to repository operations.
    """

    def __init__(self, session: Session):
        """
        Intializes the UserRepository with a SQLAlchemy session.

        Args:
            session: The SQLAlchemy Session object to use for database operations.
                     This session should be managed externally (e.g., by a middleware).
        """
        if not isinstance(session, Session):
            logger.error("UserRepository initialized without a valid SQLAlchemy Session instance.")
        self.session = session
        logger.debug("UserRepository initialized with a database session.")

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Gets a user by their primary key ID.
        """
        logger.debug(f"Fetching User by ID: {user_id}")
        try:
            return self.session.query(User).get(user_id)
        except Exception as e:
            logger.exception(f"Error fetching User by ID: {user_id}")
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Gets a user by their username.
        """
        logger.debug(f"Fetching User by username: {username}")
        try:
            return self.session.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.exception(f"Error fetching User by username: {username}")
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Gets a user by their email address.
        """
        logger.debug(f"Fetching User by email: {email}")
        try:
            return self.session.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.exception(f"Error fetching User by email: {email}")
            return None

    def list_all(self) -> List[User]:
        """
        Lists all users in the database.
        """
        logger.debug("Fetching all Users.")
        try:
            return self.session.query(User).all()
        except Exception as e:
            logger.exception("Error fetching all Users.")
            return []

    def create(self, **data: Any) -> User:
        """
        Creates a new user instance and adds it to the session.
        Note: This method adds the object to the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'user_pre_create' and 'user_post_create' signals.
        """
        logger.debug(f"Repository: Creating new User with data: {list(data.keys())}")

        signal_data = data.copy()
        if 'password' in signal_data:
            signal_data['password'] = '***'
        dispatcher.send("user_pre_create", sender=self, data=signal_data, session=self.session)
        logger.debug("Signal 'user_pre_create' sent.")

        try:
            user = User(**data)
            self.session.add(user)
            logger.info(f"Repository: User instance created and added to session (username: {data.get('username', 'N/A')}, ID: {getattr(user, 'id', 'N/A')}).")

            dispatcher.send("user_post_create", sender=self, user=user, session=self.session)
            logger.debug(f"Signal 'user_post_create' sent for User ID '{getattr(user, 'id', 'N/A')}'.")

            return user
        except Exception as e:
            logger.exception(f"Repository: Error creating User instance.")
            raise

    def update(self, user: User, **data: Any) -> User:
        """
        Updates an existing user instance with new data.
        Note: This method modifies the object in the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'user_pre_update' and 'user_post_update' signals.
        """
        user_id = getattr(user, 'id', 'N/A')
        logger.debug(f"Repository: Updating User ID {user_id} with data: {list(data.keys())}")

        signal_data = data.copy()
        if 'password' in signal_data:
            signal_data['password'] = '***'
        dispatcher.send("user_pre_update", sender=self, user=user, update_data=signal_data, session=self.session)
        logger.debug(f"Signal 'user_pre_update' sent for User ID '{user_id}'.")

        try:
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    logger.warning(f"Repository: Attempted to set non-existent attribute '{key}' on User ID {user_id}.")

            logger.info(f"Repository: User ID {user_id} updated in session.")

            dispatcher.send("user_post_update", sender=self, user=user, session=self.session)
            logger.debug(f"Signal 'user_post_update' sent for User ID '{user_id}'.")

            return user
        except Exception as e:
            logger.exception(f"Repository: Error updating User ID {user_id}.")
            raise

    def delete(self, user: User):
        """
        Deletes a user instance from the session.
        Note: This method marks the object for deletion but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'user_pre_delete' and 'user_post_delete' signals.
        """
        user_id = getattr(user, 'id', 'N/A')
        logger.debug(f"Repository: Deleting User ID {user_id}")

        dispatcher.send("user_pre_delete", sender=self, user=user, session=self.session)
        logger.debug(f"Signal 'user_pre_delete' sent for User ID '{user_id}'.")

        try:
            self.session.delete(user)
            logger.info(f"Repository: User ID {user_id} marked for deletion in session.")
            dispatcher.send("user_post_delete", sender=self, user_id=user_id, session=self.session)
            logger.debug(f"Signal 'user_post_delete' sent for User ID '{user_id}'.")
        except Exception as e:
            logger.exception(f"Repository: Error marking User ID {user_id} for deletion.")
            raise

    def search(self, **criteria: Any) -> List[User]:
        """Searches for users based on criteria."""
        logger.debug(f"Repository: Searching Users with criteria: {criteria}")
        query = self.session.query(User)
        for key, value in criteria.items():
            if hasattr(User, key):
                query = query.filter(getattr(User, key) == value)
            else:
                logger.warning(f"Repository: Search criteria '{key}' not found on User model. Skipping.")
        return query.all()

    def get_user_by_auth_token_and_expiry(self, token: str) -> Optional[User]:
        """
        Gets a user by their authentication token (e.g., password reset token)
        and ensures the token has not expired.

        Args:
            token: The authentication token.

        Returns:
            The User object if found and token is valid/not expired, otherwise None.
        """
        logger.debug(f"Fetching user by auth token (prefix: {token[:10]}...) and expiry.")
        try:
            user = self.session.query(User).filter(
                User.auth_token == token,
                User.token_expiry > datetime.utcnow()
            ).first()

            if user:
                logger.debug(f"User '{user.username}' found with valid auth token.")
            else:
                logger.debug(f"No active user found for auth token (prefix: {token[:10]}...).")
            return user
        except Exception as e:
            logger.exception(f"Error fetching user by auth token (prefix: {token[:10]}...) and expiry: {e}")
            return None

    def get_by_email_verification_token(self, token: str) -> Optional[User]:
        """
        Gets a user by their email verification token.
        Note: The expiry check for email verification token is handled within the User model's
              verify_email method to allow for more flexible expiry logic.
              This method only retrieves the user based on the token itself.

        Args:
            token: The email verification token.

        Returns:
            The User object if found, otherwise None.
        """
        logger.debug(f"Fetching user by email verification token (prefix: {token[:10]}...).")
        try:
            user = self.session.query(User).filter(
                User.email_verification_token == token
            ).first()

            if user:
                logger.debug(f"User '{user.username}' found with email verification token.")
            else:
                logger.debug(f"No user found for email verification token (prefix: {token[:10]}...).")
            return user
        except Exception as e:
            logger.exception(f"Error fetching user by email verification token (prefix: {token[:10]}...): {e}")
            return None

    def get_user_by_reset_token(self, token: str) -> Optional[User]:
        """
        Gets a user by a password reset token.
        This method is now a wrapper for get_user_by_auth_token_and_expiry.
        """
        logger.warning("UserRepository.get_user_by_reset_token is deprecated. Use get_user_by_auth_token_and_expiry instead.")
        return self.get_user_by_auth_token_and_expiry(token)

    def get_user_by_auth_token(self, token: str) -> Optional[User]:
        """
        Gets a user by an authentication token (e.g., API token).
        Note: This is different from the reset/verification token as it might not have an expiry.
        If your 'auth_token' is ONLY for password reset, use `get_user_by_auth_token_and_expiry`.
        If it's for API tokens (persistent), then this method would be relevant.
        """
        logger.debug(f"Fetching user by general auth token (prefix: {token[:10]}...).")
        try:
            user = self.session.query(User).filter(User.auth_token == token).first()
            if user:
                logger.debug(f"User '{user.username}' found with general auth token.")
            else:
                logger.debug(f"No user found for general auth token (prefix: {token[:10]}...).")
            return user
        except Exception as e:
            logger.exception(f"Error fetching user by general auth token (prefix: {token[:10]}...): {e}")
            return None