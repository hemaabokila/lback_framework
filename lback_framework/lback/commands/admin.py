import bcrypt
import logging
import sys 
from getpass import getpass
import re

from lback.models.database import DatabaseManager, Base 
from lback.repositories.user_repository import UserRepository
from lback.repositories.admin_user_repository import AdminUserRepository



logger = logging.getLogger(__name__)

class AdminCommands:
    """
    Command-line utilities for administrative tasks,
    interacting with the database using the new system.
    """

    def __init__(self):
        try:
            self.db_manager = DatabaseManager.get_instance()
        except Exception as e:
            logger.error(f"Failed to get DatabaseManager instance: {e}", exc_info=True)
            print("Error: Could not initialize database manager.", file=sys.stderr)
            sys.exit(1)

    def create_superuser(self):
        """Creates a new superuser via command line."""
        logger.info("Starting superuser creation process.")
        print("Create Superuser:")

        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = getpass("Password: ").strip()

        if not self._validate_email(email):
            logger.error("Invalid email format entered.")
            print("Error: Invalid email format.", file=sys.stderr)
            return

        session = self.db_manager.Session()
        admin_user_repo = AdminUserRepository(session)

        try:
            if admin_user_repo.get_by_username(username):
                 logger.error(f"Username '{username}' already exists.")
                 print(f"Error: Username '{username}' already exists.", file=sys.stderr)
                 return
            
            if admin_user_repo.get_by_email(email):
                 logger.error(f"Email '{email}' already exists.")
                 print(f"Error: Email '{email}' already exists.", file=sys.stderr)
                 return

            try:
                 hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            except Exception as e:
                 logger.error(f"Failed to hash password: {e}", exc_info=True)
                 print("Error: Failed to hash password.", file=sys.stderr)
                 return


            user_data = {
                 "username": username,
                 "email": email,
                 "password": hashed_password,
                 "is_superuser": True,
            }

            admin_user = admin_user_repo.create(**user_data)

            session.commit()
            logger.info(f"Superuser '{username}' created successfully.")
            print(f"Superuser '{username}' created successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating superuser: {e}", exc_info=True)
            print(f"Error creating superuser: {e}", file=sys.stderr)

        finally:
            self.db_manager.Session.remove()
            logger.debug("Session removed after create_superuser command.")


    def init_db(self):
        """
        Initializes the database schema by creating all tables.
        Note: This bypasses Alembic and is typically for initial setup or testing.
        For production, use Alembic migrations (manage.py migrate).
        """
        logger.info("🛠 Initializing Database (using create_all)...")
        print("Initializing Database...")

        try:
            self.db_manager.create_all_tables()
            logger.info("Database initialized successfully.")
            print("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            print(f"Error initializing database: {e}", file=sys.stderr)

    def reset_password(self):
        """Resets a user's password via command line."""
        logger.info("Starting password reset process.")
        print("Reset User Password:")

        username = input("Username: ").strip()

        session = self.db_manager.Session()
        user_repo = UserRepository(session)

        try:
            user = user_repo.get_by_username(username)

            if not user:
                logger.error(f"User '{username}' not found for password reset.")
                print(f"Error: User '{username}' not found.", file=sys.stderr)
                return

            password = getpass("New Password: ").strip()
            confirm = getpass("Confirm Password: ").strip()

            if password != confirm:
                logger.error("Passwords entered do not match.")
                print("Error: Passwords do not match.", file=sys.stderr)
                return

            try:
                 hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            except Exception as e:
                 logger.error(f"Failed to hash new password: {e}", exc_info=True)
                 print("Error: Failed to hash new password.", file=sys.stderr)
                 return

            user.password = hashed_password


            session.commit()
            logger.info(f"Password updated successfully for user '{username}'.")
            print(f"Password updated successfully for user '{username}'.")

        except Exception as e:
            session.rollback()
            logger.error(f"Error resetting password for user '{username}': {e}", exc_info=True)
            print(f"Error resetting password: {e}", file=sys.stderr)

        finally:
            self.db_manager.Session.remove()
            logger.debug("Session removed after reset_password command.")


    def deactivate_user(self):
        """Deactivates a user via command line."""
        logger.info("Starting user deactivation process.")
        print("Deactivate User:")

        username = input("Username: ").strip()


        session = self.db_manager.Session()
        user_repo = UserRepository(session)

        try:
            user = user_repo.get_by_username(username)

            if not user:
                logger.error(f"User '{username}' not found for deactivation.")
                print(f"Error: User '{username}' not found.", file=sys.stderr)
                return

            user.is_active = False
            session.commit()
            logger.info(f"User '{username}' deactivated successfully.")
            print(f"User '{username}' deactivated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"Error deactivating user '{username}': {e}", exc_info=True)
            print(f"Error deactivating user: {e}", file=sys.stderr)

        finally:
            self.db_manager.Session.remove()
            logger.debug("Session removed after deactivate_user command.")

    def list_users(self):
        """Lists all registered users via command line."""
        logger.info("Starting user listing process.")
        print("Listing Registered Users:")

        session = self.db_manager.Session()
        user_repo = UserRepository(session)

        try:
            users = user_repo.list_all()

            if not users:
                logger.info("No users found in the database.")
                print("No users found.")
                return

            logger.info(f"Found {len(users)} users.")
            for user in users:
                status = "Active" if getattr(user, "is_active", True) else "Inactive"
                role = "Superuser" if getattr(user, "is_superuser", False) else "Regular"
                print(f"- {user.username} ({user.email}) | Status: {status} | Role: {role}")


        except Exception as e:
            session.rollback()
            logger.error(f"Error listing users: {e}", exc_info=True)
            print(f"Error listing users: {e}", file=sys.stderr)

        finally:
            self.db_manager.Session.remove()
            logger.debug("Session removed after list_users command.")


    def activate_user(self):
        """Activates a user via command line."""
        logger.info("Starting user activation process.")
        print("Activate User:")

        username = input("Username: ").strip()
        session = self.db_manager.Session()
        user_repo = UserRepository(session)

        try:
            user = user_repo.get_by_username(username)

            if not user:
                logger.error(f"User '{username}' not found for activation.")
                print(f"Error: User '{username}' not found.", file=sys.stderr)
                return

            user.is_active = True

            session.commit()
            logger.info(f"User '{username}' activated successfully.")
            print(f"User '{username}' activated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"Error activating user '{username}': {e}", exc_info=True)
            print(f"Error activating user: {e}", file=sys.stderr)

        finally:
            self.db_manager.Session.remove()
            logger.debug("Session removed after activate_user command.")


    @staticmethod
    def _validate_email(email):
        """Validate email format."""
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(regex, email) is not None

