from sqlalchemy.orm import Session
from typing import List, Optional, Any
import logging

from lback.core.signals import dispatcher
from lback.models.adminuser import Permission

logger = logging.getLogger(__name__)

class PermissionRepository:
    """
    Repository for Permission model data access.
    Provides methods to interact with the database for Permission entities.
    Requires a SQLAlchemy Session to be provided upon initialization.
    Integrates SignalDispatcher to emit events related to repository operations.
    """

    def __init__(self, session: Session):
        """
        Initializes the PermissionRepository with a SQLAlchemy session.

        Args:
            session: The SQLAlchemy Session object to use for database operations.
                     This session should be managed externally (e.g., by a middleware).
        """
        if not isinstance(session, Session):
             logger.error("PermissionRepository initialized without a valid SQLAlchemy Session instance.")

        self.session = session
        logger.debug("PermissionRepository initialized with a database session.")

    def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """
        Gets a permission by its primary key ID.
        # No signals here, as this is a simple read operation.

        Args:
            permission_id: The integer ID of the permission.

        Returns:
            The Permission object if found, otherwise None.
        """
        logger.debug(f"Fetching Permission by ID: {permission_id}")
        return self.session.query(Permission).get(permission_id)

    def get_by_name(self, name: str) -> Optional[Permission]:
        """
        Gets a permission by its name.
        # No signals here, as this is a simple read operation.

        Args:
            name: The name string of the permission.

        Returns:
            The Permission object if found, otherwise None.
        """
        logger.debug(f"Fetching Permission by name: {name}")
        return self.session.query(Permission).filter(Permission.name == name).first()

    def list_all(self) -> List[Permission]:
        """
        Lists all permissions in the database.
        # No signals here, as this is a simple read operation.

        Returns:
            A list of all Permission objects.
        """
        logger.debug("Fetching all Permissions.")
        return self.session.query(Permission).all()

    def create(self, **data: Any) -> Permission:
        """
        Creates a new permission instance and adds it to the session.
        Note: This method adds the object to the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'permission_pre_create' and 'permission_post_create' signals.

        Args:
            **data: Keyword arguments corresponding to Permission model attributes.
                    Example: name='add_product', description='Can add new products'.

        Returns:
            The newly created Permission instance (staged in the session).

        Raises:
            Exception: For errors during instance creation or adding to session.
        """
        logger.debug(f"Repository: Creating new Permission with data: {list(data.keys())}")

        dispatcher.send("permission_pre_create", sender=self, data=data, session=self.session)
        logger.debug("Signal 'permission_pre_create' sent.")

        try:
            permission = Permission(**data)
            self.session.add(permission)
            logger.info(f"Repository: Permission instance created and added to session (name: {data.get('name', 'N/A')}, ID: {getattr(permission, 'id', 'N/A')}).")

            dispatcher.send("permission_post_create", sender=self, permission=permission, session=self.session)
            logger.debug(f"Signal 'permission_post_create' sent for Permission ID '{getattr(permission, 'id', 'N/A')}'.")

            return permission
        except Exception as e:
            logger.exception(f"Repository: Error creating Permission instance.")
            raise

    def update(self, permission: Permission, **data: Any) -> Permission:
        """
        Updates an existing permission instance with new data.
        Note: This method modifies the object in the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'permission_pre_update' and 'permission_post_update' signals.

        Args:
            permission: The Permission instance to update.
            **data: Keyword arguments for the attributes to update.
                    Example: description='Updated description'.

        Returns:
            The updated Permission instance (changes staged in the session).

        Raises:
            Exception: For errors during attribute update.
        """
        permission_id = getattr(permission, 'id', 'N/A')
        logger.debug(f"Repository: Updating Permission ID {permission_id} with data: {list(data.keys())}")

        dispatcher.send("permission_pre_update", sender=self, permission=permission, update_data=data, session=self.session)
        logger.debug(f"Signal 'permission_pre_update' sent for Permission ID '{permission_id}'.")

        try:
            for key, value in data.items():
                 if hasattr(permission, key):
                    setattr(permission, key, value)
                 else:
                    logger.warning(f"Repository: Attempted to set non-existent attribute '{key}' on Permission ID {permission_id}.")

            logger.info(f"Repository: Permission ID {permission_id} updated in session.")
            dispatcher.send("permission_post_update", sender=self, permission=permission, session=self.session)
            logger.debug(f"Signal 'permission_post_update' sent for Permission ID '{permission_id}'.")

            return permission
        except Exception as e:
            logger.exception(f"Repository: Error updating Permission ID {permission_id}.")
            raise

    def delete(self, permission: Permission):
        """
        Deletes a permission instance from the session.
        Note: This method marks the object for deletion but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'permission_pre_delete' and 'permission_post_delete' signals.

        Args:
            permission: The Permission instance to delete.

        Raises:
            Exception: For errors during marking for deletion.
        """
        permission_id = getattr(permission, 'id', 'N/A')
        logger.debug(f"Repository: Deleting Permission ID {permission_id}")

        dispatcher.send("permission_pre_delete", sender=self, permission=permission, session=self.session)
        logger.debug(f"Signal 'permission_pre_delete' sent for Permission ID '{permission_id}'.")

        try:
            self.session.delete(permission)

            logger.info(f"Repository: Permission ID {permission_id} marked for deletion in session.")

            dispatcher.send("permission_post_delete", sender=self, permission_id=permission_id, session=self.session)
            logger.debug(f"Signal 'permission_post_delete' sent for Permission ID '{permission_id}'.")

        except Exception as e:
            logger.exception(f"Repository: Error marking Permission ID {permission_id} for deletion.")
            raise

    def search(self, **criteria: Any) -> List[Permission]:
        """Searches for permissions based on criteria.
        # No signals here, as this is a read operation.
        """
        logger.debug(f"Repository: Searching Permissions with criteria: {criteria}")
        query = self.session.query(Permission)
        
        for key, value in criteria.items():
            if hasattr(Permission, key):
                query = query.filter(getattr(Permission, key) == value)
            else:
                logger.warning(f"Repository: Search criteria '{key}' not found on Permission model. Skipping.")
        return query.all()
