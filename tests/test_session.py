from lback.utils.session_manager import SessionManager
from lback.utils.user_session import UserSession
import time

def test_create_and_get_session():
    manager = SessionManager()
    session = manager.create_session(user_id=42)
    assert manager.get_session(session.session_id) == session

def test_session_expiry():
    session = UserSession(user_id=1, ttl=1)
    time.sleep(2)
    assert session.is_expired()

def test_delete_session():
    manager = SessionManager()
    session = manager.create_session(user_id=1)
    manager.delete_session(session.session_id)
    assert manager.get_session(session.session_id) is None