import logging
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from typing import Dict, Any
import json

from .base import BaseModel

logger = logging.getLogger(__name__)
class Session(BaseModel):
    """
    Represents a server-side session stored in the database.

    This model manages user session data, including session ID, associated user,
    creation and expiration timestamps, and a binary field for storing arbitrary session data.
    It provides convenient properties to serialize and deserialize the session data
    to and from a Python dictionary.
    """
    __tablename__ = 'sessions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    """The unique identifier for the session, generated as a UUID."""

    user_id = Column(String(36), nullable=True)
    """The ID of the authenticated user associated with this session. Can be None for anonymous sessions."""

    data = Column(Text, default='{}')
    """
    A text field to store arbitrary session data as a JSON string.
    This field holds dynamic session-specific information (e.g., user login status, shopping cart contents, flash messages).
    Data is serialized to JSON string before storage and deserialized from JSON string upon retrieval.
    """

    created_at = Column(DateTime, default=datetime.utcnow)
    """The timestamp when the session was created."""

    expires_at = Column(DateTime, nullable=False)
    """The timestamp when the session is scheduled to expire."""

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    """The timestamp of the last update to the session. Automatically updated on record modification."""

    def __repr__(self):
        """
        Provides a string representation of the Session object for debugging purposes.
        """
        return f"<Session(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}')>"

    @property
    def data_dict(self) -> Dict[str, Any]:
        """
        Deserializes the binary 'data' field into a Python dictionary.

        This property handles the conversion of the stored binary data back into
        a usable dictionary format, making it easy to access session variables.
        It uses `pickle` for deserialization.

        :returns: The session data as a dictionary, or an empty dictionary if no data is stored.
        :rtype: Dict[str, Any]
        """
        try:
            return json.loads(self.data) if self.data else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON data for session {self.id}. Returning empty dict.", exc_info=True)
            return {}

    @data_dict.setter
    def data_dict(self, value: Dict[str, Any]):
        """
        Serializes a Python dictionary into binary data and stores it in the 'data' field.

        This setter allows you to assign a dictionary directly to the `data_dict` property,
        and it will automatically serialize the dictionary into bytes using `pickle`
        for storage in the database.

        :param value: The dictionary of data to be stored in the session.
        :type value: Dict[str, Any]
        """
        self.data = json.dumps(value)