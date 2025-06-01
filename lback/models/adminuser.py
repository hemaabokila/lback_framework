import logging
from typing import Set
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship

from lback.core.signals import dispatcher
from .base import BaseModel

logger = logging.getLogger(__name__)

role_permission = Table(
    'role_permission',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.id'), primary_key=True)
)

class AdminUser(BaseModel):
    """
    Represents an administrative user in the system.
    Admin users can have roles and permissions.
    """
    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=True)

    role = relationship("Role", back_populates="admin_users")

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the AdminUser."""
        return f"<AdminUser(id={self.id}, username='{self.username}', email='{self.email}', is_superuser={self.is_superuser})>"

    def has_permission(self, permission_name: str) -> bool:
        """
        Checks if the admin user has a specific permission.
        Superusers have all permissions. Otherwise, checks the user's role's permissions.
        Emits 'admin_user_permission_checked' signal.

        Args:
            permission_name: The name string of the permission to check.

        Returns:
            True if the user has the permission, False otherwise.
        """
        logger.debug(f"Checking permission '{permission_name}' for user '{self.username}'.")

        has_perm = False
        reason = "default_false"

        if self.is_superuser:
            logger.debug(f"User '{self.username}' is superuser, has permission '{permission_name}'.")
            has_perm = True
            reason = "is_superuser"
        elif self.role and hasattr(self.role, 'permissions') and isinstance(self.role.permissions, list):
            has_perm = any(permission.name == permission_name for permission in self.role.permissions if hasattr(permission, 'name'))
            logger.debug(f"User '{self.username}' (Role: {getattr(self.role, 'name', 'N/A')}) permission check for '{permission_name}': {has_perm}.")
            reason = "found_in_role_permissions" if has_perm else "not_found_in_role_permissions"
        else:
            logger.debug(f"User '{self.username}' has no role or no permissions defined on role. Does not have permission '{permission_name}'.")
            reason = "no_role_or_permissions"

        dispatcher.send("admin_user_permission_checked", sender=self, admin_user=self, permission_name=permission_name, has_permission=has_perm, reason=reason)
        logger.debug(f"Signal 'admin_user_permission_checked' sent for user '{self.username}', permission '{permission_name}'. Result: {has_perm}, Reason: {reason}.")

        return has_perm
    @property
    def permissions(self) -> Set[str]:
        """
        Returns a set of permission names associated with this user's role.
        This property is used by the PermissionRequired decorator.
        """
        if self.is_superuser:
            return {"*"}
        
        if self.role:
            return {p.name for p in self.role.permissions}
        
        return set()


class Permission(BaseModel):
    """
    Represents a specific permission that can be assigned to roles.
    """
    __tablename__ = 'permission'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)

    roles = relationship("Role", secondary=role_permission, back_populates="permissions")

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the Permission."""
        return f"<Permission(id={self.id}, name='{self.name}')>"


class Role(BaseModel):
    """
    Represents a role that groups multiple permissions.
    Admin users can be assigned roles.
    """
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)

    permissions = relationship("Permission", secondary=role_permission, back_populates="roles")
    admin_users = relationship("AdminUser", back_populates="role")

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the Role."""
        return f"<Role(id={self.id}, name='{self.name}')>"

    def add_permission(self, permission: Permission):
        """
        Adds a permission to this role.
        Emits 'role_permission_added' signal on success.
        Emits 'role_permission_operation_failed' signal on failure (invalid type, already exists).

        Args:
            permission: The Permission object to add.
        """
        logger.debug(f"Attempting to add permission '{getattr(permission, 'name', 'N/A')}' to role '{self.name}'.")
        if not isinstance(permission, Permission):
             logger.warning(f"Attempted to add non-Permission object to role '{self.name}'. Type: {type(permission)}.")
             dispatcher.send("role_permission_operation_failed", sender=self, role=self, operation="add", permission=permission, error_type="invalid_type")
             logger.debug(f"Signal 'role_permission_operation_failed' (add_invalid_type) sent for role '{self.name}'.")
             return

        if permission not in self.permissions:
            self.permissions.append(permission)
            logger.info(f"Permission '{permission.name}' added to role '{self.name}'.")
            dispatcher.send("role_permission_added", sender=self, role=self, permission=permission)
            logger.debug(f"Signal 'role_permission_added' sent for role '{self.name}', permission '{permission.name}'.")
        else:
            logger.debug(f"Permission '{permission.name}' already exists in role '{self.name}'. Skipping add.")
            dispatcher.send("role_permission_operation_failed", sender=self, role=self, operation="add", permission=permission, error_type="already_exists")
            logger.debug(f"Signal 'role_permission_operation_failed' (add_already_exists) sent for role '{self.name}', permission '{permission.name}'.")


    def remove_permission(self, permission: Permission):
        """
        Removes a permission from this role.
        Emits 'role_permission_removed' signal on success.
        Emits 'role_permission_operation_failed' signal on failure (invalid type, not found).

        Args:
            permission: The Permission object to remove.
        """
        logger.debug(f"Attempting to remove permission '{getattr(permission, 'name', 'N/A')}' from role '{self.name}'.")
        if not isinstance(permission, Permission):
             logger.warning(f"Attempted to remove non-Permission object from role '{self.name}'. Type: {type(permission)}.")
             dispatcher.send("role_permission_operation_failed", sender=self, role=self, operation="remove", permission=permission, error_type="invalid_type")
             logger.debug(f"Signal 'role_permission_operation_failed' (remove_invalid_type) sent for role '{self.name}'.")
             return

        if permission in self.permissions:
            self.permissions.remove(permission)
            logger.info(f"Permission '{permission.name}' removed from role '{self.name}'.")
            dispatcher.send("role_permission_removed", sender=self, role=self, permission=permission)
            logger.debug(f"Signal 'role_permission_removed' sent for role '{self.name}', permission '{permission.name}'.")
        else:
            logger.debug(f"Permission '{permission.name}' not found in role '{self.name}'. Skipping removal.")
            dispatcher.send("role_permission_operation_failed", sender=self, role=self, operation="remove", permission=permission, error_type="not_found")
            logger.debug(f"Signal 'role_permission_operation_failed' (remove_not_found) sent for role '{self.name}', permission '{permission.name}'.")
