from sqlalchemy.orm import Session
from typing import List, Optional, Any
import logging


from lback.core.signals import dispatcher
from lback.models.adminuser import AdminUser

logger = logging.getLogger(__name__)

class AdminUserRepository:
    """
    Repository for AdminUser model data access.
    Provides methods to interact with the database for AdminUser entities.
    Requires a SQLAlchemy Session to be provided upon initialization.
    Integrates SignalDispatcher to emit events related to repository operations.
    """

    def __init__(self, session: Session):
        """
        Initializes the AdminUserRepository with a SQLAlchemy session.

        Args:
            session: The SQLAlchemy Session object to use for database operations.
                     This session should be managed externally (e.g., by a middleware).
        """
        if not isinstance(session, Session):
             logger.error("AdminUserRepository initialized without a valid SQLAlchemy Session instance.")

        self.session = session
        logger.debug("AdminUserRepository initialized with a database session.")


    def get_by_id(self, admin_user_id: int) -> Optional[AdminUser]:
        """
        Gets an admin user by their primary key ID.
        # No signals here, as this is a simple read operation.

        Args:
            admin_user_id: The integer ID of the admin user.

        Returns:
            The AdminUser object if found, otherwise None.
        """
        logger.debug(f"Fetching AdminUser by ID: {admin_user_id}")
        return self.session.query(AdminUser).get(admin_user_id)

    def get_by_username(self, username: str) -> Optional[AdminUser]:
        """
        Gets an admin user by their username.
        # No signals here, as this is a simple read operation.

        Args:
            username: The username string of the admin user.

        Returns:
            The AdminUser object if found, otherwise None.
        """
        logger.debug(f"Fetching AdminUser by username: {username}")
        return self.session.query(AdminUser).filter(AdminUser.username == username).first()

    def get_by_email(self, email: str) -> Optional[AdminUser]:
        """
        Gets an admin user by their email address.
        # No signals here, as this is a simple read operation.

        Args:
            email: The email address string of the admin user.

        Returns:
            The AdminUser object if found, otherwise None.
        """
        logger.debug(f"Fetching AdminUser by email: {email}")
        return self.session.query(AdminUser).filter(AdminUser.email == email).first()

    def list_all(self) -> List[AdminUser]:
        """
        Lists all admin users in the database.
        # No signals here, as this is a simple read operation.

        Returns:
            A list of all AdminUser objects.
        """
        logger.debug("Fetching all AdminUsers.")
        return self.session.query(AdminUser).all()

    def create(self, **data: Any) -> AdminUser:
        """
        Creates a new admin user instance and adds it to the session.
        Note: This method adds the object to the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'admin_user_pre_create' and 'admin_user_post_create' signals.

        Args:
            **data: Keyword arguments corresponding to AdminUser model attributes.
                    Example: username='admin', email='a@example.com', password='hashed_password'.

        Returns:
            The newly created AdminUser instance (staged in the session).

        Raises:
            Exception: If an error occurs during instance creation or adding to session.
        """
        logger.debug(f"Repository: Creating new AdminUser with data: {list(data.keys())}")

        signal_data = data.copy()
        if 'password' in signal_data:
             signal_data['password'] = '***'
        dispatcher.send("admin_user_pre_create", sender=self, data=signal_data, session=self.session)
        logger.debug("Signal 'admin_user_pre_create' sent.")

        try:
            admin_user = AdminUser(**data)
            self.session.add(admin_user)

            logger.info(f"Repository: AdminUser instance created and added to session (username: {data.get('username', 'N/A')}, ID: {getattr(admin_user, 'id', 'N/A')}).")


            dispatcher.send("admin_user_post_create", sender=self, admin_user=admin_user, session=self.session)
            logger.debug(f"Signal 'admin_user_post_create' sent for AdminUser ID '{getattr(admin_user, 'id', 'N/A')}'.")

            return admin_user
        except Exception as e:
            logger.exception(f"Repository: Error creating AdminUser instance.")
            raise


    def update(self, admin_user: AdminUser, **data: Any) -> AdminUser:
        """
        Updates an existing admin user instance with new data.
        Note: This method modifies the object in the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'admin_user_pre_update' and 'admin_user_post_update' signals.

        Args:
            admin_user: The AdminUser instance to update.
            **data: Keyword arguments for the attributes to update.
                    Example: email='new_email@example.com', is_active=False.

        Returns:
            The updated AdminUser instance (changes staged in the session).

        Raises:
            Exception: If an error occurs during the update process.
        """
        admin_user_id = getattr(admin_user, 'id', 'N/A')
        logger.debug(f"Repository: Updating AdminUser ID {admin_user_id} with data: {list(data.keys())}")

        signal_data = data.copy()
        if 'password' in signal_data:
             signal_data['password'] = '***'
        dispatcher.send("admin_user_pre_update", sender=self, admin_user=admin_user, update_data=signal_data, session=self.session)
        logger.debug(f"Signal 'admin_user_pre_update' sent for AdminUser ID '{admin_user_id}'.")

        try:
            for key, value in data.items():
                if hasattr(admin_user, key):
                    setattr(admin_user, key, value)
                else:
                    logger.warning(f"Repository: Attempted to set non-existent attribute '{key}' on AdminUser ID {admin_user_id}.")

            logger.info(f"Repository: AdminUser ID {admin_user_id} updated in session.")

            dispatcher.send("admin_user_post_update", sender=self, admin_user=admin_user, session=self.session)
            logger.debug(f"Signal 'admin_user_post_update' sent for AdminUser ID '{admin_user_id}'.")
            return admin_user
        
        except Exception as e:
            logger.exception(f"Repository: Error updating AdminUser ID {admin_user_id}.")
            raise


    def delete(self, admin_user: AdminUser):
        """
        Deletes an admin user instance from the session.
        Note: This method marks the object for deletion but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'admin_user_pre_delete' and 'admin_user_post_delete' signals.

        Args:
            admin_user: The AdminUser instance to delete.

        Raises:
            Exception: If an error occurs during the deletion process.
        """
        admin_user_id = getattr(admin_user, 'id', 'N/A')
        logger.debug(f"Repository: Deleting AdminUser ID {admin_user_id}")

        dispatcher.send("admin_user_pre_delete", sender=self, admin_user=admin_user, session=self.session)
        logger.debug(f"Signal 'admin_user_pre_delete' sent for AdminUser ID '{admin_user_id}'.")

        try:
            self.session.delete(admin_user)

            logger.info(f"Repository: AdminUser ID {admin_user_id} marked for deletion in session.")

            dispatcher.send("admin_user_post_delete", sender=self, admin_user_id=admin_user_id, session=self.session)
            logger.debug(f"Signal 'admin_user_post_delete' sent for AdminUser ID '{admin_user_id}'.")

        except Exception as e:
            logger.exception(f"Repository: Error marking AdminUser ID {admin_user_id} for deletion.")
            raise

    def search(self, **criteria: Any) -> List[AdminUser]:
        """
        Searches for admin users based on criteria.
        # No signals here, as this is a read operation.
        """
        logger.debug(f"Repository: Searching AdminUsers with criteria: {criteria}")

        query = self.session.query(AdminUser)

        for key, value in criteria.items():
            if hasattr(AdminUser, key):
                query = query.filter(getattr(AdminUser, key) == value)
            else:
                logger.warning(f"Repository: Search criteria '{key}' not found on AdminUser model. Skipping.")
        return query.all()

    def get_admin_by_reset_token(self, token: str) -> Optional[AdminUser]:
        """Gets an admin user by a password reset token.
        # Assuming this method exists and works. No signals added here,
        # as token validation/lookup signals might be handled elsewhere (e.g., UserManager).
        """
        logger.warning("Repository: get_admin_by_reset_token is not implemented.")
        pass

