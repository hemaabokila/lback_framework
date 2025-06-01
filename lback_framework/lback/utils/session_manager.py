from datetime import datetime, timedelta
import logging
import secrets
import json
from typing import Any, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError


from lback.core.types import Request
from lback.core.signals import dispatcher
from lback.models.session import Session as DBSessionModel

logger = logging.getLogger(__name__)

SessionDataType = Dict[str, Any]

class SessionManager:
    """
    Manages server-side sessions using a persistent database store.
    Receives the request-scoped database session per method call.
    Integrates SignalDispatcher to emit events related to session lifecycle and operations.
    """

    def __init__(self, timeout_minutes: int = 30):
        """
        Initializes the SessionManager.
        Emits 'session_manager_initialized' signal.

        Args:
            timeout_minutes: The duration in minutes after which a session expires
                             if not renewed. Defaults to 30 minutes.
        """
        if not isinstance(timeout_minutes, int) or timeout_minutes <= 0:
            logger.error(f"Invalid timeout_minutes value: {timeout_minutes}. Must be a positive integer. Using default 30.")
            self.session_timeout = timedelta(minutes=30)
        else:
            self.session_timeout = timedelta(minutes=timeout_minutes)

        logger.info(f"SessionManager initialized with timeout: {self.session_timeout}.")
        if dispatcher:
            dispatcher.send("session_manager_initialized", sender=self, timeout=self.session_timeout)
        else:
            logger.warning("Dispatcher is None. Cannot send 'session_manager_initialized' signal.")

    def create_session(self, db_session: DBSession, user_id: Optional[str] = None) -> Optional[str]:
        """
        Creates a new session record in the database and returns its ID.

        This method generates a unique session ID, sets its creation and expiration
        timestamps, and initializes its data payload as an empty JSON string.
        The session is flushed to the database to ensure the ID is available immediately.

        Args:
            db_session: The SQLAlchemy Session for database operations.
            user_id: An optional user ID to associate with the session upon creation.
                     This value will be stored directly in the `user_id` column of the Session model.

        Returns:
            The newly generated unique session ID (string) if successful, otherwise None.
        """
        logger.debug(f"SessionManager: Creating new session for user_id: {user_id}")
        try:
            new_session = DBSessionModel(
                user_id=user_id,
                expires_at=datetime.utcnow() + self.session_timeout,
                data=json.dumps({})
            )
            db_session.add(new_session)
            db_session.flush()
            logger.debug(f"SessionManager: New session object added, ID: {new_session.id}")
            return new_session.id
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"SessionManager: Failed to create session: {e}", exc_info=True)
            return None

    def get(self, request: Request, db_session: DBSession, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieves a specific value from the session data based on the request and key, using the database.
        This method extracts the session ID from the request (e.g., from a cookie)
        and then retrieves the value from the session data in the database.
        Relies on get_session_data which emits signals.

        Args:
            request: The incoming request object.
            db_session: The SQLAlchemy Session for database operations.
            key: The key for the data to retrieve from the session.
            default: The value to return if the key is not found or session is invalid.

        Returns:
            The value associated with the key in the session data, or the default value
            if the session is not found/expired or the key is not present.
        """
        session_id = self._get_session_id_from_request(request)
        if not session_id:
            logger.debug(f"SessionManager.get: No session ID found in request for key '{key}'. Returning default.")
            return default
        session_data_dict = self.get_session_data(db_session, session_id)
        if session_data_dict is None:
            logger.debug(f"SessionManager.get: Session data not found or expired for ID {session_id} for key '{key}'. Returning default.")
            return default
        try:
            session_data_payload = json.loads(session_data_dict.get('data', b'{}').decode('utf-8'))
            value = session_data_payload.get(key, default)
            logger.debug(f"SessionManager.get: Retrieved value for key '{key}' from session {session_id}: {value}")
            return value
        except json.JSONDecodeError:
             logger.error(f"SessionManager.get: Failed to decode JSON data for session ID {session_id}. Key: '{key}'. Returning default.", exc_info=True)
             return default

    def _get_session_id_from_request(self, request: Request) -> Optional[str]:
        """
        Extracts the session ID from the request (e.g., from the 'Cookie' header).
        # No signals here, as this is a low-level parsing utility.

        Args:
            request: The incoming request object.

        Returns:
            The session ID string if found in the cookie, otherwise None.
        """
        cookie_header = request.headers.get('COOKIE')
        if not cookie_header:
            logger.debug("SessionManager: No 'COOKIE' header in request.")
            return None

        cookies: Dict[str, str] = {}
        try:
            cookie_list = [c.strip() for c in cookie_header.split(';')]
            for cookie_pair in cookie_list:
                if '=' in cookie_pair:
                    key, value = cookie_pair.split('=', 1)
                    cookies[key] = value
        except Exception as e:
            logger.error(f"SessionManager: Error parsing 'COOKIE' header: {e}")
            return None

        session_id = cookies.get('session_id')

        if session_id:
            logger.debug(f"SessionManager: Found session ID in cookie: {session_id}")
            return session_id
        
        else:
            logger.debug("SessionManager: 'session_id' cookie not found in header.")
            return None

    def get_user(self, db_session: DBSession, session_id: str) -> Optional[Any]:
        """
        Gets the user ID associated with a session ID from the database, if the session is valid.
        Relies on get_session_data which emits signals.

        Args:
            db_session: The SQLAlchemy Session for database operations.
            session_id: The ID of the session.

        Returns:
            The user ID if the session is valid, otherwise None.
        """
        logger.debug(f"Attempting to get user ID for session ID: {session_id}")

        session_data = self.get_session_data(db_session, session_id)
        if session_data:
            try:
                session_payload = json.loads(session_data.get('data', b'{}').decode('utf-8'))
                user_id = session_payload.get('user_id')
                logger.debug(f"User ID {user_id} found for valid session {session_id}.")
                return user_id
            
            except json.JSONDecodeError:
                logger.error(f"SessionManager.get_user: Failed to decode JSON data for session ID {session_id}. Returning None.", exc_info=True)
                return None
            
        logger.debug(f"No valid session found for ID {session_id} to get user ID.")
        return None

    def get_session_data(self, db_session: DBSession, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the full session data dictionary for a given session ID from the database.

        This method queries the database for an active (non-expired) session.
        If found, it returns a dictionary containing all session details, including
        the raw JSON string from the 'data' column.

        Args:
            db_session: The SQLAlchemy Session for database operations.
            session_id: The unique ID of the session to retrieve.

        Returns:
            A dictionary containing session details ('id', 'user_id', 'created_at',
            'expires_at', 'updated_at', and 'data' as a JSON string) if the session
            is valid and active, otherwise None.
        """
        logger.debug(f"SessionManager: Attempting to get session data for ID: {session_id}")
        session_obj = db_session.query(DBSessionModel).filter(
            DBSessionModel.id == session_id,
            DBSessionModel.expires_at > datetime.utcnow()
        ).first()
        if session_obj:
            logger.debug(f"SessionManager: Session object found for ID: {session_id}. Data type in DB: {type(session_obj.data)}")
            return {
                'id': session_obj.id,
                'user_id': session_obj.user_id,
                'data': session_obj.data, 
                'created_at': session_obj.created_at,
                'expires_at': session_obj.expires_at,
                'updated_at': session_obj.updated_at
            }
        logger.debug(f"SessionManager: No active session found for ID: {session_id}")
        return None
    
    def save_session_data(self, db_session: DBSession, session_id: str, data_dict: Dict[str, Any]) -> bool:
        """
        Saves or updates the entire data payload (as a dictionary) for a specific session in the database.

        This method serializes the provided Python dictionary (`data_dict`) into a JSON string
        and stores it in the 'data' column of the session record. It also renews the session's
        expiration time.

        Args:
            db_session: The SQLAlchemy Session for database operations.
            session_id: The unique ID of the session to update.
            data_dict: The dictionary containing all session data to be stored.

        Returns:
            True if the session was found and its data was successfully saved, False otherwise.
        """
        logger.debug(f"SessionManager: Saving full data dict for session ID: {session_id}. Keys: {list(data_dict.keys())}")
        session_obj = db_session.query(DBSessionModel).filter_by(id=session_id).first()
        if session_obj:
            try:
                session_obj.data = json.dumps(data_dict)
                session_obj.expires_at = datetime.utcnow() + self.session_timeout
                db_session.flush()
                logger.debug(f"SessionManager: Successfully saved data for session ID: {session_id}")
                return True
            except Exception as e:
                logger.error(f"SessionManager: Failed to save data for session ID {session_id}: {e}", exc_info=True)
                return False
        logger.warning(f"SessionManager: Attempted to save data for non-existent session ID: {session_id}")
        return False

    def set_session_data(self, db_session: DBSession, session_id: str, key: str, value: Any):
        """
        Sets a key-value pair within the 'data' dictionary of a valid session in the database.
        This method is used for storing custom session data (like flash messages).
        Emits 'session_data_set' signal on success.
        Emits 'session_operation_failed' signal on failure (session not found/expired).
        Args:
            db_session: The SQLAlchemy Session for database operations.
            session_id: The ID of the session to update.
            key: The key for the data item within the session's 'data' dictionary.
            value: The value to store. Setting value to None might indicate deletion
                   depending on how you want to handle it (current implementation stores None).
        """
        logger.debug(f"Attempting to set data key '{key}' for session ID: {session_id}")
        try:
            session_record = db_session.query(DBSessionModel).filter(DBSessionModel.id == session_id).first()
            if session_record:
                try:
                    session_data_payload = json.loads(session_record.data.decode('utf-8'))
                except (json.JSONDecodeError, AttributeError):
                    logger.error(f"SessionManager.set_session_data: Failed to decode JSON data for session ID {session_id}. Initializing 'data' dict.", exc_info=True)
                    if dispatcher:
                         dispatcher.send("session_operation_failed", sender=self, session_id=session_id, operation="set_data_invalid_structure", key=key, error_type="invalid_data_structure")
                    else:
                        logger.warning("Dispatcher is None. Cannot send 'session_operation_failed' signal.")
                    session_data_payload = {}
                session_data_payload[key] = value
                session_record.data = json.dumps(session_data_payload).encode('utf-8')
                session_record.updated_at = datetime.utcnow()
                db_session.flush()
                logger.debug(f"Set data key '{key}' in session {session_id}.")
                if dispatcher:
                    dispatcher.send("session_data_set", sender=self, session_id=session_id, key=key, value=value)
                else:
                    logger.warning("Dispatcher is None. Cannot send 'session_data_set' signal.")
            else:
                logger.warning(f"Failed to set data for session {session_id}: Session not found.")
                if dispatcher:
                     dispatcher.send("session_operation_failed", sender=self, session_id=session_id, operation="set_data", key=key, error_type="not_found")
                else:
                    logger.warning("Dispatcher is None. Cannot send 'session_operation_failed' signal.")
        except SQLAlchemyError as e:
            logger.error(f"Database error setting data key '{key}' for session {session_id}: {e}", exc_info=True)
            db_session.rollback()
            if dispatcher:
                 dispatcher.send("session_operation_failed", sender=self, session_id=session_id, operation="set_data", key=key, error_type="db_error", exception=e)
            else:
                logger.warning("Dispatcher is None. Cannot send 'session_operation_failed' signal.")
        except Exception as e:
            logger.error(f"Unexpected error setting data key '{key}' for session {session_id}: {e}", exc_info=True)
            db_session.rollback()
            if dispatcher:
                 dispatcher.send("session_operation_failed", sender=self, session_id=session_id, operation="set_data", key=key, error_type="unexpected_error", exception=e)

            else:
                logger.warning("Dispatcher is None. Cannot send 'session_operation_failed' signal.")

    def is_session_expired(self, session: Dict[str, Any]) -> bool:
        """
        Checks if a session dictionary is expired based on its 'expires_at' timestamp.
        # No signals here, as this is an internal helper method.
        Args:
            session: The session dictionary retrieved from storage (or SQLAlchemy model).
                     Expected to have an 'expires_at' key which is a datetime object.
        Returns:
            True if the session is expired, False otherwise.
        """
        if 'expires_at' not in session or not isinstance(session.get('expires_at'), datetime):
            logger.error(f"Session dictionary missing or has invalid 'expires_at' for session with user_id: {session.get('user_id', 'N/A')}. Treating as expired.")
            return True
        return datetime.utcnow() > session['expires_at']

    def renew_session(self, db_session: DBSession, session_id: str) -> bool:
        """
        Renews the expiration time of an existing session in the database.
        This typically happens automatically with every request to keep active sessions alive.

        Args:
            db_session: The SQLAlchemy database session object.
            session_id: The unique ID of the session to renew.

        Returns:
            True if the session was found and successfully renewed, False otherwise.
        """
        logger.debug(f"SessionManager: Renewing session ID: {session_id}")
        session_obj = db_session.query(DBSessionModel).filter_by(id=session_id).first()
        if session_obj:
            session_obj.expires_at = datetime.utcnow() + self.session_timeout
            db_session.flush()
            logger.debug(f"SessionManager: Session ID {session_id} renewed.")
            return True
        logger.debug(f"SessionManager: No session found to renew for ID: {session_id}")
        return False

    def delete_session(self, db_session: DBSession, session_id: str) -> bool:
        """
        Deletes a specific session from the database.
        This is typically used during user logout or when a session needs to be invalidated.

        Args:
            db_session: The SQLAlchemy database session object.
            session_id: The unique ID of the session to delete.

        Returns:
            True if the session was found and successfully deleted, False otherwise.
        """
        logger.debug(f"SessionManager: Deleting session ID: {session_id}")
        session_obj = db_session.query(DBSessionModel).filter_by(id=session_id).first()
        if session_obj:
            db_session.delete(session_obj)
            db_session.flush()
            logger.debug(f"SessionManager: Session ID {session_id} deleted.")
            return True
        logger.debug(f"SessionManager: No session found to delete for ID: {session_id}")
        return False

    def cleanup_sessions(self, db_session: DBSession):
        """
        Removes all expired sessions from the database.
        This method should be called periodically (e.g., by a background task).
        Emits 'session_cleanup_started' and 'session_cleanup_finished' signals.
        """
        logger.info("Starting session cleanup.")
        if dispatcher:
            dispatcher.send("session_cleanup_started", sender=self)
        else:
            logger.warning("Dispatcher is None. Cannot send 'session_cleanup_started' signal.")
        try:
            now = datetime.utcnow()
            expired_sessions = db_session.query(DBSessionModel).filter(DBSessionModel.expires_at < now).all()
            deleted_count = 0
            for session_record in expired_sessions:
                session_dict = {
                    'id': session_record.id,
                    'user_id': session_record.user_id,
                    'created_at': session_record.created_at,
                    'expires_at': session_record.expires_at,
                    'data': session_record.data
                }
                if self.is_session_expired(session_dict):
                    db_session.delete(session_record)
                    deleted_count += 1
            db_session.flush()
            logger.info(f"Session cleanup completed. {deleted_count} sessions removed from DB.")
            if dispatcher:
                dispatcher.send("session_cleanup_finished", sender=self, removed_count=deleted_count)
            else:
                logger.warning("Dispatcher is None. Cannot send 'session_cleanup_finished' signal.")

        except SQLAlchemyError as e:
            logger.error(f"Database error during session cleanup: {e}", exc_info=True)
            db_session.rollback()
            if dispatcher:
                 dispatcher.send("session_operation_failed", sender=self, operation="cleanup", error_type="db_error", exception=e)
            else:
                logger.warning("Dispatcher is None. Cannot send 'session_operation_failed' signal.")

        except Exception as e:
            logger.error(f"Unexpected error during session cleanup: {e}", exc_info=True)
            db_session.rollback()
            if dispatcher:
                 dispatcher.send("session_operation_failed", sender=self, operation="cleanup", error_type="unexpected_error", exception=e)
            else:
                logger.warning("Dispatcher is None. Cannot send 'session_operation_failed' signal.")

    def generate_csrf_token(self, db_session: DBSession, session_id: str) -> Optional[str]:
        """
        Generates a new CSRF token, stores it in the session data in the database, and returns it.
        Emits 'csrf_token_generated' signal on success.
        Emits 'session_operation_failed' signal on failure (session not found/expired).

        Args:
            db_session: The SQLAlchemy Session for database operations.
            session_id: The ID of the session to associate the token with.

        Returns:
            The generated CSRF token string if the session is valid, otherwise None.
        """
        logger.debug(f"Attempting to generate CSRF token for session ID: {session_id}")
        session_data_dict = self.get_session_data(db_session, session_id)
        if session_data_dict:
            csrf_token = secrets.token_hex(32)
            self.set_session_data(db_session, session_id, "csrf_token", csrf_token)
            logger.debug(f"Generated and stored CSRF token for session {session_id}.")
            if dispatcher:
                dispatcher.send("csrf_token_generated", sender=self, session_id=session_id, csrf_token=csrf_token)
            else:
                logger.warning("Dispatcher is None. Cannot send 'csrf_token_generated' signal.")
            return csrf_token
        else:
            logger.warning(f"Failed to generate CSRF token: Session {session_id} not found or expired.")
            return None

    def validate_csrf_token(self, db_session: DBSession, session_id: str, csrf_token: str) -> bool:
        """
        Validates the provided CSRF token against the one stored in the session in the database.
        Emits 'csrf_token_validated' signal on success.
        Emits 'csrf_token_validation_failed' signal on failure.
        Args:
            db_session: The SQLAlchemy Session for database operations.
            session_id: The ID of the session to validate the token against.
            csrf_token: The token provided in the request (e.g., from form data or header).

        Returns:
            True if the session is valid and the provided token matches the stored token, False otherwise.
        """
        logger.debug(f"Attempting to validate CSRF token for session ID: {session_id}")
        session_data_dict = self.get_session_data(db_session, session_id)

        if session_data_dict is None:
            logger.debug(f"Failed to validate CSRF token: Session data not found or expired for ID {session_id}.")
            if dispatcher:
                dispatcher.send("csrf_token_validation_failed", sender=self, session_id=session_id, error_type="session_invalid")
            else:
                logger.warning("Dispatcher is None. Cannot send 'csrf_token_validation_failed' signal.")
            return False

        try:
            session_data_payload = json.loads(session_data_dict.get('data', b'{}').decode('utf-8'))
            stored_token = session_data_payload.get("csrf_token")
        except json.JSONDecodeError:
             logger.error(f"SessionManager.validate_csrf_token: Failed to decode JSON data for session ID {session_id}. Returning False.", exc_info=True)
             if dispatcher:
                 dispatcher.send("csrf_token_validation_failed", sender=self, session_id=session_id, error_type="json_decode_error")
             else:
                logger.warning("Dispatcher is None. Cannot send 'csrf_token_validation_failed' signal.")
             return False
        
        if stored_token and isinstance(stored_token, str) and isinstance(csrf_token, str) and secrets.compare_digest(stored_token, csrf_token):
            logger.debug(f"CSRF token validated successfully for session {session_id}.")
            if dispatcher:
                dispatcher.send("csrf_token_validated", sender=self, session_id=session_id)
            else:
                logger.warning("Dispatcher is None. Cannot send 'csrf_token_validated' signal.")
            return True
        
        else:
            logger.debug(f"CSRF token validation failed for session {session_id}. Stored token present: {stored_token is not None}.")
            if dispatcher:
                dispatcher.send("csrf_token_validation_failed", sender=self, session_id=session_id, error_type="token_mismatch", stored_token_present=(stored_token is not None))
            else:
                logger.warning("Dispatcher is None. Cannot send 'csrf_token_validation_failed' signal.")
            return False

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the SessionManager."""
        return f"<SessionManager(timeout={self.session_timeout}, storage='Database')>"