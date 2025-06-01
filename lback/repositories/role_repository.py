from sqlalchemy.orm import Session
from typing import List, Optional, Any
import logging

from lback.core.signals import dispatcher 
from lback.models.adminuser import Role

logger = logging.getLogger(__name__)

class RoleRepository:
    """
    Repository for Role model data access.
    Provides methods to interact with the database for Role entities.
    Requires a SQLAlchemy Session to be provided upon initialization.
    Integrates SignalDispatcher to emit events related to repository operations.
    """

    def __init__(self, session: Session):
        """
        Initializes the RoleRepository with a SQLAlchemy session.

        Args:
            session: The SQLAlchemy Session object to use for database operations.
                     This session should be managed externally (e.g., by a middleware).
        """
        if not isinstance(session, Session):
             logger.error("RoleRepository initialized without a valid SQLAlchemy Session instance.")

        self.session = session
        logger.debug("RoleRepository initialized with a database session.")

    def get_by_id(self, role_id: int) -> Optional[Role]:
        """
        Gets a role by its primary key ID.
        # No signals here, as this is a simple read operation.

        Args:
            role_id: The integer ID of the role.

        Returns:
            The Role object if found, otherwise None.
        """
        logger.debug(f"Fetching Role by ID: {role_id}")
        return self.session.query(Role).get(role_id)

    def get_by_name(self, name: str) -> Optional[Role]:
        """
        Gets a role by its name.
        # No signals here, as this is a simple read operation.

        Args:
            name: The name string of the role.

        Returns:
            The Role object if found, otherwise None.
        """
        logger.debug(f"Fetching Role by name: {name}")
        return self.session.query(Role).filter(Role.name == name).first()

    def list_all(self) -> List[Role]:
        """
        Lists all roles in the database.
        # No signals here, as this is a simple read operation.

        Returns:
            A list of all Role objects.
        """
        logger.debug("Fetching all Roles.")
        return self.session.query(Role).all()

    def create(self, **data: Any) -> Role:
        """
        Creates a new role instance and adds it to the session.
        Note: This method adds the object to the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'role_pre_create' and 'role_post_create' signals.

        Args:
            **data: Keyword arguments corresponding to Role model attributes.
                    Example: name='editor', description='Can edit content'.

        Returns:
            The newly created Role instance (staged in the session).

        Raises:
            Exception: For errors during instance creation or adding to session.
        """
        logger.debug(f"Repository: Creating new Role with data: {list(data.keys())}")

        dispatcher.send("role_pre_create", sender=self, data=data, session=self.session)
        logger.debug("Signal 'role_pre_create' sent.")

        try:
            role = Role(**data)
            self.session.add(role)

            logger.info(f"Repository: Role instance created and added to session (name: {data.get('name', 'N/A')}).")

            dispatcher.send("role_post_create", sender=self, role=role, session=self.session)
            logger.debug(f"Signal 'role_post_create' sent for Role ID '{getattr(role, 'id', 'N/A')}'.")

            return role
        except Exception as e:
            logger.exception(f"Repository: Error creating Role instance.")
            raise

    def update(self, role: Role, **data: Any) -> Role:
        """
        Updates an existing role instance with new data.
        Note: This method modifies the object in the session but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'role_pre_update' and 'role_post_update' signals.

        Args:
            role: The Role instance to update.
            **data: Keyword arguments for the attributes to update.
                    Example: description='Updated description'.

        Returns:
            The updated Role instance (changes staged in the session).

        Raises:
            Exception: For errors during attribute update.
        """
        role_id = getattr(role, 'id', 'N/A')
        logger.debug(f"Repository: Updating Role ID {role_id} with data: {list(data.keys())}")

        dispatcher.send("role_pre_update", sender=self, role=role, update_data=data, session=self.session)
        logger.debug(f"Signal 'role_pre_update' sent for Role ID '{role_id}'.")

        try:
            for key, value in data.items():
                 if hasattr(role, key):
                    setattr(role, key, value)
                 else:
                    logger.warning(f"Repository: Attempted to set non-existent attribute '{key}' on Role ID {role_id}.")

            logger.info(f"Repository: Role ID {role_id} updated in session.")

            dispatcher.send("role_post_update", sender=self, role=role, session=self.session)
            logger.debug(f"Signal 'role_post_update' sent for Role ID '{role_id}'.")

            return role
        except Exception as e:
            logger.exception(f"Repository: Error updating Role ID {role_id}.")
            raise

    def delete(self, role: Role):
        """
        Deletes a role instance from the session.
        Note: This method marks the object for deletion but does NOT commit.
        The caller is responsible for committing the session.
        Emits 'role_pre_delete' and 'role_post_delete' signals.

        Args:
            role: The Role instance to delete.

        Raises:
            Exception: For errors during marking for deletion.
        """
        role_id = getattr(role, 'id', 'N/A')
        logger.debug(f"Repository: Deleting Role ID {role_id}")
        dispatcher.send("role_pre_delete", sender=self, role=role, session=self.session)
        logger.debug(f"Signal 'role_pre_delete' sent for Role ID '{role_id}'.")

        try:
            self.session.delete(role)

            logger.info(f"Repository: Role ID {role_id} marked for deletion in session.")
            dispatcher.send("role_post_delete", sender=self, role_id=role_id, session=self.session)
            logger.debug(f"Signal 'role_post_delete' sent for Role ID '{role_id}'.")

        except Exception as e:
            logger.exception(f"Repository: Error marking Role ID {role_id} for deletion.")
            raise

    def search(self, **criteria: Any) -> List[Role]:
        """Searches for roles based on criteria.
        # No signals here, as this is a read operation.
        """
        logger.debug(f"Repository: Searching Roles with criteria: {criteria}")
        
        query = self.session.query(Role)
        for key, value in criteria.items():
            if hasattr(Role, key):
                query = query.filter(getattr(Role, key) == value)
            else:
                logger.warning(f"Repository: Search criteria '{key}' not found on Role model. Skipping.")
        return query.all()