import logging
from typing import Optional , Any
from http import HTTPStatus
from sqlalchemy.orm import Session as DBSession

from lback.core.base_middleware import BaseMiddleware
from lback.core.response import Response
from lback.core.types import Request
from lback.models.database import DatabaseManager



logger = logging.getLogger(__name__)

class SQLAlchemySessionMiddleware(BaseMiddleware):
    """
    Middleware to manage a SQLAlchemy database session for each request.
    Creates a new session at the start of the request and closes it at the end.
    Attaches the session to the request context using the key 'db_session'.
    Handles transaction management (commit or rollback) based on request outcome.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes with a DatabaseManager instance (a dependency).

        Args:
            db_manager: The DatabaseManager instance for session creation.
        """
        if not isinstance(db_manager, DatabaseManager):
             logger.error("SQLAlchemySessionMiddleware initialized without a valid DatabaseManager instance.")


        self.db_manager = db_manager
        logger.info("SQLAlchemySessionMiddleware initialized.")

    def process_request(self, request: Request) -> Optional[Response]:
        """
        Creates a new database session and attaches it to the request context.
        """
        logger.debug(f"SQLAlchemySessionMiddleware: Creating DB session for {request.method} {request.path}")
        db_session = None

        try:
            session_object_from_manager = self.db_manager.create_session()

            logger.debug(f"SQLAlchemySessionMiddleware: Object returned by create_session. Type: {type(session_object_from_manager)}, Repr: {repr(session_object_from_manager)}")

            if isinstance(session_object_from_manager, DBSession):
                 db_session = session_object_from_manager
                 logger.debug("SQLAlchemySessionMiddleware: create_session returned a valid SQLAlchemy Session.")
            else:
                 logger.error(f"SQLAlchemySessionMiddleware: create_session did NOT return a SQLAlchemy Session. Returned type: {type(session_object_from_manager)}")

            if hasattr(request, 'add_context') and callable(request.add_context):
                 request.add_context('db_session', db_session)
                 logger.debug(f"SQLAlchemySessionMiddleware: Attached DB session ({type(db_session)}) to request context using add_context.")
            elif hasattr(request, '_context') and isinstance(request._context, dict):
                 request._context['db_session'] = db_session
                 logger.debug(f"SQLAlchemySessionMiddleware: Attached DB session ({type(db_session)}) to request context using _context dictionary.")
            else:
                 logger.error("SQLAlchemySessionMiddleware: Request object does not support adding context data. Cannot attach DB session.")

            logger.debug("SQLAlchemySessionMiddleware: DB session creation and attachment process finished.")
            return None

        except Exception as e:
            logger.error(f"SQLAlchemySessionMiddleware: Error during DB session creation process for {request.method} {request.path}: {e}", exc_info=True)
            return Response(body=b"Internal Server Error: Error during database session creation process.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value)


    def process_response(self, request: Request, response: Response) -> Response:
        """
        Commits or rolls back the database session and closes it at the end of the request.
        Commits if no exception occurred, rolls back if an exception occurred during request processing.
        """
        logger.debug(f"SQLAlchemySessionMiddleware: Processing response for {request.method} {request.path}")

        db_session_from_context: Optional[Any] = request.get_context('db_session')

        logger.debug(f"SQLAlchemySessionMiddleware: Retrieved object from context['db_session']. Value: {db_session_from_context}, Type: {type(db_session_from_context)}, Repr: {repr(db_session_from_context)}")

        if isinstance(db_session_from_context, DBSession):
            db_session: DBSession = db_session_from_context
            logger.debug("SQLAlchemySessionMiddleware: Retrieved object from context is a valid SQLAlchemy Session.")

            try:
                request_exception = request.get_context('exception')

                if request_exception:
                    logger.warning(f"SQLAlchemySessionMiddleware: Exception detected in request context ({type(request_exception).__name__}). Rolling back DB session.")
                    db_session.rollback()
                    logger.debug("SQLAlchemySessionMiddleware: DB session rolled back.")

                else:
                    logger.debug("SQLAlchemySessionMiddleware: No exception detected. Committing DB session.")
                    db_session.commit()
                    logger.debug("SQLAlchemySessionMiddleware: DB session committed.")

            except Exception as e:
                logger.error(f"SQLAlchemySessionMiddleware: Error during DB session commit/rollback for {request.method} {request.path}: {e}", exc_info=True)
                try:
                    db_session.rollback()
                    logger.warning("SQLAlchemySessionMiddleware: Attempted rollback after commit/rollback error.")

                except Exception as rollback_e:
                    logger.error(f"SQLAlchemySessionMiddleware: Error during rollback after commit/rollback error: {rollback_e}", exc_info=True)

            finally:

                try:
                    db_session.close()
                    logger.debug("SQLAlchemySessionMiddleware: DB session closed.")
                except Exception as close_e:
                    logger.error(f"SQLAlchemySessionMiddleware: Error closing DB session: {close_e}", exc_info=True)

        elif db_session_from_context is None:
             logger.debug("SQLAlchemySessionMiddleware: No object found in request context['db_session']. Skipping commit/rollback/close.")

        else:
             logger.error(f"SQLAlchemySessionMiddleware: Object in request context['db_session'] is NOT a SQLAlchemy Session or None. Type: {type(db_session_from_context)}, Repr: {repr(db_session_from_context)}. Cannot process session.")


        logger.debug("SQLAlchemySessionMiddleware: Finished processing response.")
        return response

