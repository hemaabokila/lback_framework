import logging
import json
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session as DBSession
from datetime import datetime

from lback.utils.session_manager import SessionManager

logger = logging.getLogger(__name__)

class AppSession:
    """
    Represents the session data for a single request, stored in the database.
    Provides a dictionary-like interface and interacts with the SessionManager.
    """

    def __init__(self, session_id: Optional[str], initial_data: Optional[Dict[str, Any]], session_manager: SessionManager, db_session: DBSession, is_new: bool = False, expires_at: Optional[datetime] = None):
        """
        Initializes the Session wrapper.
        Args:
            session_id: The ID of the session (None if it's a new, unsaved session).
            initial_data: The dictionary containing the actual session 'data' (or None for a new session).
                          This data is typically loaded from the DB by SessionMiddleware.
            session_manager: The SessionManager instance used for saving/deleting.
            db_session: The SQLAlchemy Session for database operations for this request.
            is_new: Boolean indicating if this is a newly created session that needs saving and a cookie.
            expires_at: The datetime when the session expires, loaded from the database.
        """
        self._session_id = session_id
        self._data = initial_data if initial_data is not None else {}
        self._session_manager = session_manager
        self._db_session = db_session
        self._is_new = is_new
        self._modified = False
        self._deleted = False
        self.expires_at = expires_at

        logger.debug(f"AppSession initialized: ID={self._session_id}, IsNew={self._is_new}, ExpiresAt={self.expires_at}, InitialDataKeys={list(self._data.keys())}")

    @property
    def session_id(self) -> Optional[str]:
        """Returns the session ID, or None if it's a new unsaved session."""
        return self._session_id

    @property
    def is_new(self) -> bool:
        """Returns True if this is a newly created session."""
        return self._is_new

    @property
    def modified(self) -> bool:
        """Returns True if the session data has been modified during the request."""
        return self._modified

    @property
    def deleted(self) -> bool:
        """Returns True if the session has been marked for deletion."""
        return self._deleted

    def __getitem__(self, key: str) -> Any:
        """Gets a value from the session data using item access (e.g., session['user_id'])."""
        logger.debug(f"AppSession: Getting item '{key}' from local data for session {self._session_id}.")
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        """Sets a value in the session data using item assignment (e.g., session['user_id'] = 123)."""
        logger.debug(f"AppSession: Setting item '{key}' for session {self._session_id}. Marking session as modified.")
        self._data[key] = value
        self._modified = True

    def __delitem__(self, key: str):
        """Deletes a key from the session data using item deletion (e.g., del session['user_id'])."""
        logger.debug(f"AppSession: Deleting item '{key}' for session {self._session_id}. Marking session as modified.")
        if key in self._data:
            del self._data[key]
            self._modified = True
        else:
            logger.warning(f"AppSession: Attempted to delete non-existent key '{key}' from session data for session {self._session_id}.")


    def __contains__(self, key: Any) -> bool:
        """Checks if a key exists in the session data (e.g., 'user_id' in session)."""
        return key in self._data

    def __len__(self) -> int:
        """Returns the number of items in the session data."""
        length = len(self._data)
        logger.debug(f"AppSession.__len__: Called for session {self._session_id}. Returning length: {length}. Data Keys: {list(self._data.keys())}")
        return length



    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Gets a value from the session data using the get() method."""
        return self._data.get(key, default)

    def pop(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Removes a key and returns its value."""
        logger.debug(f"AppSession: Popping item '{key}' for session {self._session_id}. Marking session as modified.")
        value = self._data.pop(key, default)
        self._modified = True
        return value

    def clear(self):
        """Clears all data from the session."""
        logger.debug("AppSession: Clearing all local session data. Marking session as modified.")
        self._data.clear()
        self._modified = True

    def keys(self):
        """Returns a view object that displays a list of all the keys in the dictionary."""
        return self._data.keys()

    def values(self):
        """Returns a view object that displays a list of all the values in the dictionary."""
        return self._data.values()

    def items(self):
        """Returns a view object that displays a list of a dictionary's key-value tuple pairs."""
        return self._data.items()

    def __iter__(self):
        """Returns an iterator for the session data keys."""
        return iter(self._data)


    def __str__(self) -> str:
        """Provides a user-friendly string representation of the session data."""
        return str(self._data)

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the Session wrapper."""
        status = "New" if self._is_new else "Existing"
        modified_status = "Modified" if self._modified else "Unmodified"
        deleted_status = "Deleted" if self._deleted else "Not Deleted"
        return f"<Session(id={self._session_id or 'None'}, status='{status}', modified='{modified_status}', deleted='{deleted_status}', keys={list(self._data.keys())})>"

    def save(self) -> Optional[str]:
        """
        Saves the current session data to the database using the SessionManager.
        If it's a new session, it will be created. If modified, it will be updated.
        Returns:
            The session ID if save was successful, None otherwise.
        """
        if self._deleted:
            logger.debug("AppSession.save: Session marked as deleted. Skipping save attempt.")
            return None
        
        if self._is_new:
            logger.debug("AppSession.save: Attempting to create and save new session in DB.")
            try:
                user_id_for_new_session = self._data.get('user_id')
                new_session_id = self._session_manager.create_session(self._db_session, user_id=user_id_for_new_session)

                if not new_session_id:
                    logger.error("AppSession.save: SessionManager.create_session failed to return a session ID. Cannot proceed with save.")
                    return None

                self._session_id = new_session_id
                self._is_new = False
                
                if self._data:
                    logger.debug(f"AppSession.save: Saving initial data payload to newly created session {self._session_id}.")
                    self._session_manager.save_session_data(self._db_session, self._session_id, self._data)
                    self._modified = False

                logger.debug(f"AppSession.save: New session created and data saved with ID {self._session_id}.")
                return self._session_id

            except Exception as e:
                logger.error(f"AppSession.save: Failed during new session creation or initial data save process: {e}", exc_info=True)
                
                if self._session_id:
                    logger.warning(f"AppSession.save: Attempting to delete incomplete new session {self._session_id} due to error.")
                    self._session_manager.delete_session(self._db_session, self._session_id)
                
                self._deleted = True
                return None
            
        elif self._modified and self._session_id:
            logger.debug(f"AppSession.save: Session {self._session_id} is modified. Saving data to DB.")
            try:
                self._session_manager.save_session_data(self._db_session, self._session_id, self._data)
                self._modified = False
                logger.debug(f"AppSession.save: Data saved for modified session {self._session_id}.")
                return self._session_id
            except Exception as e:
                logger.error(f"AppSession.save: Failed to save modified session {self._session_id} to DB: {e}", exc_info=True)
                return None

        else:
            logger.debug(f"AppSession.save: Session {self._session_id or 'None'} not modified or already deleted. No save needed.")
            return self._session_id

    def delete(self):
        """
        Deletes the session using the SessionManager and marks the local object as deleted.
        """
        if self._session_id and not self._deleted:
            logger.debug(f"AppSession.delete: Attempting to delete session {self._session_id} from DB.")
            try:
                success = self._session_manager.delete_session(self._db_session, self._session_id)
                if success:
                    self._session_id = None
                    self._data = {}
                    self._is_new = False
                    self._modified = False
                    self._deleted = True
                    logger.debug("AppSession.delete: Session deleted successfully from DB and object state reset.")
                else:
                    logger.warning(f"AppSession.delete: SessionManager.delete_session failed for ID {self._session_id}.")

            except Exception as e:
                logger.error(f"AppSession.delete: Failed to delete session {self._session_id} from DB: {e}", exc_info=True)

        elif self._deleted:
            logger.debug("AppSession.delete: Session already marked as deleted. No action needed.")

        else:
            logger.debug("AppSession.delete: Session is new and not saved yet. Clearing local data and marking as deleted.")
            self._session_id = None
            self._data = {}
            self._is_new = False
            self._modified = False
            self._deleted = True
            logger.debug("AppSession.delete: New session data cleared locally.")


    def set_flash(self, message: str, category: str = 'info'):
        """
        Adds a flash message to the session. Flash messages are typically displayed
        once on the next request and then cleared.
        """
        logger.debug(f"AppSession: Attempting to add flash message: '{message}' ({category}).")
        FLASH_MESSAGES_KEY = 'flash_messages'
        flash_messages: list = self.get(FLASH_MESSAGES_KEY, [])

        if not isinstance(flash_messages, list):
            logger.warning(f"AppSession: Data for '{FLASH_MESSAGES_KEY}' is not a list (type: {type(flash_messages)}). Initializing as empty list.")
            flash_messages = []

        flash_messages.append({'message': message, 'category': category})
        self[FLASH_MESSAGES_KEY] = flash_messages
        logger.debug(f"AppSession: Added flash message. Total messages now: {len(flash_messages)}.")

    def get_flashed_messages(self, category_filter: Optional[str] = None) -> list[Dict[str, str]]:
        """
        Retrieves all flashed messages from the session and clears them.
        Optionally filters messages by category.
        """
        logger.debug("AppSession: Attempting to retrieve flashed messages.")
        FLASH_MESSAGES_KEY = 'flash_messages'
        flash_messages: list = self.get(FLASH_MESSAGES_KEY, [])

        if not isinstance(flash_messages, list):
            logger.warning(f"AppSession: Data for '{FLASH_MESSAGES_KEY}' is not a list (type: {type(flash_messages)}). Returning empty list and clearing invalid data.")
            self[FLASH_MESSAGES_KEY] = []
            return []

        flashed_messages: list[Dict[str, str]] = []
        remaining_messages: list[Dict[str, str]] = []

        for msg in flash_messages:
            if isinstance(msg, dict) and 'message' in msg and 'category' in msg:
                if category_filter is None or msg.get('category') == category_filter:
                    flashed_messages.append(msg)

                else:
                    remaining_messages.append(msg)
            else:
                logger.warning(f"AppSession: Found malformed flash message in session data: {msg}. Skipping.")

        if category_filter:
            self[FLASH_MESSAGES_KEY] = remaining_messages
            logger.debug(f"AppSession: Retrieved {len(flashed_messages)} flashed messages (filter: {category_filter}). Remaining: {len(remaining_messages)}.")
        else:
            if FLASH_MESSAGES_KEY in self._data:
                 del self[FLASH_MESSAGES_KEY]
                 logger.debug(f"AppSession: Cleared all flashed messages for session {self._session_id}.")

        return flashed_messages
    
    def load(self) -> bool:
        """
        Loads session data from the database using the SessionManager.
        Returns True if a session was loaded, False otherwise.
        """
        if self._session_id:
            session_data_from_db = self._session_manager.get_session_data(self._db_session, self._session_id)

            if session_data_from_db:
                try:
                    self._data = json.loads(session_data_from_db.get('data', '{}'))
                    self._is_new = False
                    self._modified = False
                    self._deleted = False
                    self.expires_at = session_data_from_db.get('expires_at')
                    logger.debug(f"AppSession.load: Session data loaded successfully for ID {self._session_id}. ExpiresAt: {self.expires_at}. Data keys: {list(self._data.keys())}")
                    return True
                except json.JSONDecodeError:
                    logger.error(f"AppSession.load: Failed to decode JSON data for session ID {self._session_id}. Treating as not loaded.", exc_info=True)
                    self._data = {}
                    self._is_new = True
                    self._modified = True
                    self._deleted = False
                    self.expires_at = None
                    return False
            else:
                logger.debug(f"AppSession.load: Session ID {self._session_id} not found or expired in DB.")
                self._data = {}
                self._is_new = True
                self._modified = True
                self._deleted = False
                self.expires_at = None
                return False
        else:
            logger.debug("AppSession.load: No session ID set. Cannot load.")
            self._data = {}
            self._is_new = True
            self._modified = False
            self._deleted = False
            self.expires_at = None
            return False

    def invalidate(self):
        """Marks the session for deletion."""
        logger.debug(f"AppSession: Invalidating session {self._session_id or 'None'}. Marking for deletion.")
        self._deleted = True
        self._modified = False
        self._data = {} 
        self.expires_at = datetime.utcnow()


