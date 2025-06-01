from sqlalchemy import create_engine, exc
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
import logging
from typing import Optional, Any
from sqlalchemy.orm import Session as DBSession

from lback.core.config import Config
from lback.core.signals import dispatcher


try:
    from .base import Base
except ImportError:
    logging.warning("Could not import Base from .models. Assuming Base is defined elsewhere or using declarative_base() directly here.")
    Base = declarative_base()


logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages the database connection and session factory as a singleton.
    Responsible for creating the SQLAlchemy engine and providing a scoped session factory
    for managing database sessions within the application context (e.g., per request).
    Emits signals for key database lifecycle events.
    """

    _instance: Optional['DatabaseManager'] = None
    _initialized: bool = False

    def __init__(self):
        """
        Initializes the DatabaseManager.
        This constructor should ideally only be called once via get_instance().
        It sets up the database engine and session factory based on Config settings.
        Emits 'db_manager_initialized' signal on success.
        Emits 'db_operation_failed' signal on initialization failure.
        """
        if self._initialized:
            logger.debug("DatabaseManager already initialized. Skipping __init__.")
            return

        logger.info("Initializing DatabaseManager...")
        try:
            config = Config()
            database_url: str = config.DATABASE_URI
            echo_queries: bool = config.DATABASE_ECHO

            self._engine = create_engine(
                database_url,
                echo=echo_queries,
            )
            logger.info("SQLAlchemy engine created.")

            self._session_factory = sessionmaker(bind=self._engine)
            logger.debug("Session factory created.")

            self._scoped_session = scoped_session(self._session_factory)
            logger.debug("Scoped session factory created.")

            self._initialized = True
            logger.info("DatabaseManager initialized successfully.")

            dispatcher.send("db_manager_initialized", sender=self, manager=self)
            logger.debug("Signal 'db_manager_initialized' sent.")

        except Exception as e:
            logger.error(f"Error initializing DatabaseManager: {e}", exc_info=True)
            self._engine = None
            self._session_factory = None
            self._scoped_session = None

            dispatcher.send("db_operation_failed", sender=self, manager=self, operation="initialization", exception=e)
            logger.debug("Signal 'db_operation_failed' (initialization) sent.")

            raise RuntimeError("Failed to initialize DatabaseManager.") from e
    def create_session(self) -> DBSession:
        """
        Creates and returns a new SQLAlchemy database session using the scoped session factory.
        This method is intended to be called once per request by the SQLAlchemySessionMiddleware.
        """
        if not self._initialized or self._scoped_session is None:
            logger.error("Attempted to create session before DatabaseManager was successfully initialized.")
            raise RuntimeError("DatabaseManager is not initialized. Cannot create session.")

        logger.debug("DatabaseManager: Creating new database session from scoped factory.")

        return self._scoped_session()
    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        """
        Gets the singleton instance of the DatabaseManager.
        Initializes the manager if it hasn't been already.

        Returns:
            The singleton DatabaseManager instance.
        """
        if cls._instance is None:
            logger.debug("DatabaseManager instance not found. Creating new instance.")
            cls._instance = cls()
        else:
            logger.debug("Returning existing DatabaseManager instance.")
        return cls._instance

    @property
    def engine(self) -> Optional[Any]:
        """
        Returns the SQLAlchemy engine instance.

        Returns:
            The SQLAlchemy engine, or None if initialization failed.
        """
        if not self._initialized or self._engine is None:
             logger.warning("Attempted to access engine before DatabaseManager was successfully initialized.")
             return None
        return self._engine

    @property
    def Session(self) -> Optional[Any]:
        """
        Returns the scoped session factory.
        Calling this property returns the factory function that provides the current session
        for the calling thread/context.

        Returns:
            The scoped session factory, or None if initialization failed.
        """
        if not self._initialized or self._scoped_session is None:
             logger.warning("Attempted to access Session factory before DatabaseManager was successfully initialized.")
             return None
        return self._scoped_session

    def create_all_tables(self):
        """
        Creates all database tables defined by the models associated with Base.metadata.
        Requires the engine to be successfully initialized.
        Emits 'db_tables_created' signal on success.
        Emits 'db_operation_failed' signal on failure.
        """
        logger.info("Creating database tables...")
        if self.engine is None:
             logger.error("Cannot create tables: Database engine is not initialized.")
             raise RuntimeError("Cannot create tables: Database engine not available.")

        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tables created successfully.")
            dispatcher.send("db_tables_created", sender=self, manager=self)
            logger.debug("Signal 'db_tables_created' sent.")

        except exc.SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error creating tables: {e}", exc_info=True)
            dispatcher.send("db_operation_failed", sender=self, manager=self, operation="create_tables", exception=e)
            logger.debug("Signal 'db_operation_failed' (create_tables) sent.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while creating tables: {e}")
            dispatcher.send("db_operation_failed", sender=self, manager=self, operation="create_tables_unexpected", exception=e)
            logger.debug("Signal 'db_operation_failed' (create_tables_unexpected) sent.")
            raise


    def drop_all_tables(self):
        """
        Drops all database tables defined by the models associated with Base.metadata.
        Use with caution, as this will delete all data.
        Requires the engine to be successfully initialized.
        Emits 'db_tables_dropped' signal on success.
        Emits 'db_operation_failed' signal on failure.
        """
        logger.warning("Dropping database tables... ALL DATA WILL BE LOST!")
        if self.engine is None:
             logger.error("Cannot drop tables: Database engine is not initialized.")
             raise RuntimeError("Cannot drop tables: Database engine not available.")

        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped successfully.")
            dispatcher.send("db_tables_dropped", sender=self, manager=self)
            logger.debug("Signal 'db_tables_dropped' sent.")

        except exc.SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error dropping tables: {e}", exc_info=True)
            dispatcher.send("db_operation_failed", sender=self, manager=self, operation="drop_tables", exception=e)
            logger.debug("Signal 'db_operation_failed' (drop_tables) sent.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while dropping tables: {e}")
            dispatcher.send("db_operation_failed", sender=self, manager=self, operation="drop_tables_unexpected", exception=e)
            logger.debug("Signal 'db_operation_failed' (drop_tables_unexpected) sent.")
            raise


    def dispose_engine(self):
        """
        Disposes the database engine's connection pool.
        This should be called on application shutdown to release database connections.
        Emits 'db_engine_disposed' signal on success.
        Emits 'db_operation_failed' signal on failure.
        """
        logger.info("Disposing database engine...")
        if self._engine:
            try:
                self._engine.dispose()
                logger.info("Engine disposed successfully.")
                dispatcher.send("db_engine_disposed", sender=self, manager=self)
                logger.debug("Signal 'db_engine_disposed' sent.")
            except Exception as e:
                 logger.error(f"Error disposing database engine: {e}", exc_info=True)
                 dispatcher.send("db_operation_failed", sender=self, manager=self, operation="dispose_engine", exception=e)
                 logger.debug("Signal 'db_operation_failed' (dispose_engine) sent.")
        else:
            logger.warning("Attempted to dispose engine, but engine was not initialized.")

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the DatabaseManager."""
        status = "Initialized" if self._initialized else "Not Initialized"
        engine_status = "Available" if self._engine else "None"
        return f"<DatabaseManager(status='{status}', engine='{engine_status}')>"

