import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Set, ClassVar

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import validates, relationship
from sqlalchemy.ext.declarative import declarative_base 

from lback.core.signals import dispatcher
from lback.auth.password_hashing import PasswordHasher
from .base import BaseModel 

logger = logging.getLogger(__name__)


Base = declarative_base()

user_groups_association = Table(
    'user_groups_association', BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

group_permissions_association = Table(
    'group_permissions_association', BaseModel.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('userpermissions.id'), primary_key=True)

)



class Group(BaseModel):
    """
    Represents a group or role that users can belong to.
    A group has a name and can be associated with multiple permissions.
    """
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)


    permissions = relationship(
        'UserPermission',
        secondary=group_permissions_association,
        backref='groups',
        lazy='dynamic'
    )

    def __repr__(self) -> str:
        return f"<Group(id={self.id}, name='{self.name}')>"

class UserPermission(BaseModel): 
    """
    Represents a specific permission that can be granted to groups.
    """
    __tablename__ = 'userpermissions' 
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<UserPermission(id={self.id}, name='{self.name}')>"


class User(BaseModel):
    """
    Represents a regular application user.
    Extends BaseModel with user-specific fields and validation.
    Now supports Many-to-Many relationship with Groups for flexible role management.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String, nullable=True, index=True)
    email_verification_token_expiry = Column(DateTime, nullable=True)
    auth_token = Column(String, nullable=True, index=True)
    token_expiry = Column(DateTime, nullable=True)

    groups = relationship(
        'Group',
        secondary=user_groups_association,
        backref='users',
        lazy='dynamic'
    )

    _user_permissions_cache: ClassVar[Dict[int, Set[str]]] = {}
    _last_permissions_update: ClassVar[Optional[datetime]] = None
    _CACHE_EXPIRY_SECONDS: ClassVar[int] = 300

    @validates('username')
    def validate_username(self, key: str, value: Optional[str]) -> str:
        if not value or not isinstance(value, str) or len(value.strip()) == 0:
            logger.error("Validation failed for username: Value is empty.")
            raise ValueError("Username cannot be empty.")
        if len(value.strip()) < 3:
            logger.error(f"Validation failed for username '{value}': Too short.")
            raise ValueError("Username must be at least 3 characters long.")
        return value.strip()

    @validates('email')
    def validate_email(self, key: str, value: Optional[str]) -> str:
        if not value or not isinstance(value, str) or len(value.strip()) == 0:
            logger.error("Validation failed for email: Value is empty.")
            raise ValueError("Email cannot be empty.")
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, value.strip()):
            logger.error(f"Validation failed for email '{value}': Invalid format.")
            raise ValueError("Invalid email format.")
        return value.strip()

    @validates('password')
    def validate_password(self, key: str, value: Optional[str]) -> str:
        if not value or not isinstance(value, str) or len(value.strip()) == 0:
            logger.error("Validation failed for password: Value is empty (hashed password).")
            raise ValueError("Password (hashed) cannot be empty.")
        return value

    def set_password(self, plain_password: str):
        """
        Hashes the plain text password and sets it on the model.
        Emits 'user_password_set' signal on success, 'user_password_set_failed' on failure.
        """
        user_id = getattr(self, 'id', 'N/A')
        username = getattr(self, 'username', 'N/A')
        logger.info(f"Attempting to set password for user '{username}' (ID: {user_id}).")

        try:
            hashed_password = PasswordHasher.hash_password(plain_password)
            self.password = hashed_password
            logging.info(f"Password set (hashed) for user '{username}' (ID: {user_id}).")
            dispatcher.send("user_password_set", sender=self, user=self)
            logger.debug(f"Signal 'user_password_set' sent for user '{username}'.")
        except Exception as e:
            logging.exception(f"Error hashing or setting password for user '{username}' (ID: {user_id}): {e}")
            dispatcher.send("user_password_set_failed", sender=self, user=self, exception=e)
            logger.debug(f"Signal 'user_password_set_failed' sent for user '{username}'.")
            raise

    def check_password(self, plain_password: str) -> bool:
        """
        Checks the provided plain text password against the stored hashed password.
        Emits 'user_password_checked' signal after the check, 'user_password_check_failed' on error.
        """
        user_id = getattr(self, 'id', 'N/A')
        username = getattr(self, 'username', 'N/A')
        logger.info(f"Checking password for user '{username}' (ID: {user_id}).")

        result = False
        try:
            if self.password:
                result = PasswordHasher.verify_password(plain_password, self.password)
                logging.info(f"Password check for user '{username}' (ID: {user_id}): {'Success' if result else 'Failure'}.")
            else:
                logging.warning(f"Password check failed for user '{username}' (ID: {user_id}): Stored password is None.")
                result = False
            dispatcher.send("user_password_checked", sender=self, user=self, success=result)
            logger.debug(f"Signal 'user_password_checked' sent for user '{username}'. Success: {result}.")
            return result
        except Exception as e:
            logging.exception(f"Error checking password for user '{username}' (ID: {user_id}): {e}")
            dispatcher.send("user_password_check_failed", sender=self, user=self, exception=e)
            logger.debug(f"Signal 'user_password_check_failed' sent for user '{username}'.")
            return False

    def generate_email_verification_token(self, expiry_minutes: int = 60):
        """
        Generates a new email verification token and sets its expiry.
        """
        self.email_verification_token = PasswordHasher.generate_random_token()
        self.email_verification_token_expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        logger.info(f"Email verification token generated for user '{self.username}'.")
        dispatcher.send("user_email_verification_token_generated", sender=self, user=self)

    def verify_email(self, token: str) -> bool:
        """
        Verifies the provided email verification token and marks email as verified if valid.
        """
        if self.email_verification_token and self.email_verification_token == token and \
           self.email_verification_token_expiry and datetime.utcnow() < self.email_verification_token_expiry:
            self.is_email_verified = True
            self.email_verification_token = None
            self.email_verification_token_expiry = None
            logger.info(f"Email verified successfully for user '{self.username}'.")
            dispatcher.send("user_email_verified", sender=self, user=self)
            return True
        logger.warning(f"Email verification failed for user '{self.username}'. Invalid or expired token.")
        dispatcher.send("user_email_verification_failed", sender=self, user=self)
        return False

    @property
    def is_admin(self) -> bool:
        """
        Determines if the user is an admin based on their group membership.
        Assumes there's a group named 'admin'.
        """
        return any(group.name == 'admin' for group in self.groups)

    @property
    def is_superuser(self) -> bool:
        """
        Determines if the user is a superuser.
        This can be based on a specific group or a dedicated flag in the User model.
        For simplicity, we'll assume 'admin' group implies superuser for now.
        In a real app, you might have a separate `is_superuser` column.
        """
        return self.is_admin

    @property
    def user_type(self) -> str:
        """
        Returns the general type of the user ('user' or 'admin').
        The AuthMiddleware uses this general type to differentiate between
        regular users and admin users handled by separate managers.
        Specific roles (like 'premium_user', 'editor', 'basic_user') should
        be checked via `has_permission` or `groups_names` property.
        """

        if self.is_admin:
            return "admin"
        return "user"

    def has_permission(self, permission_name: str) -> bool:
        """
        Checks if the user has a specific permission by checking their groups' permissions.
        Uses a class-level cache to improve performance.
        """
        if not self.is_active or not self.is_email_verified:
            return False

        if self.is_superuser:
            return True

        user_id = self.id
        current_time = datetime.utcnow()

        if user_id in User._user_permissions_cache and \
           User._last_permissions_update and \
           (current_time - User._last_permissions_update).total_seconds() < User._CACHE_EXPIRY_SECONDS:
            
            cached_permissions = User._user_permissions_cache[user_id]
            logger.debug(f"has_permission: Using cached permissions for user {user_id}. Checking '{permission_name}'.")
            return permission_name in cached_permissions
        
        logger.debug(f"has_permission: Cache miss or expired for user {user_id}. Fetching permissions from DB.")
        
        user_permissions_set = set()
        for group in self.groups:
            for perm in group.permissions:
                user_permissions_set.add(perm.name)

        User._user_permissions_cache[user_id] = user_permissions_set
        User._last_permissions_update = current_time

        logger.debug(f"has_permission: Fetched and cached permissions for user {user_id}: {user_permissions_set}. Checking '{permission_name}'.")
        return permission_name in user_permissions_set

    @classmethod
    def get_fields(cls) -> Dict[str, str]:
        """
        Returns a dictionary of column names and their SQLAlchemy types for this model.
        Useful for introspection, e.g., in generic admin views.
        """
        return {column.name: str(column.type) for column in cls.__table__.columns}

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the User instance."""
        return (f"<User(id={getattr(self, 'id', 'N/A')}, username='{getattr(self, 'username', 'N/A')}', "
                f"email='{getattr(self, 'email', 'N/A')}', is_active={getattr(self, 'is_active', 'N/A')}, "
                f"is_email_verified={getattr(self, 'is_email_verified', 'N/A')})>")
