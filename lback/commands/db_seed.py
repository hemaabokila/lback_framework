import logging

from lback.models.user import Group, UserPermission

logger = logging.getLogger(__name__)

def setup_database_and_defaults(db_manager_instance):
    """
    Initializes the database schema and populates it with default groups and permissions.
    This should be called as part of a dedicated 'seed_db' command.
    """
    logger.info("Starting database setup and default data population...")
    
    db_session = db_manager_instance.get_session()
    
    try:
        UserPermission.create_defaults(db_session)
        Group.create_defaults(db_session)

        logger.info("Database setup and default data population completed successfully.")

    except Exception as e:
        logger.error(f"Failed to create default groups/permissions: {e}", exc_info=True)
        db_session.rollback()
        raise
    finally:
        db_session.close()
