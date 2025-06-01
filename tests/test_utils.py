import pytest
from lback.utils.validation import ValidationError
from lback.utils.session_manager import SessionManager
from lback.utils.user_session import UserSession
from lback.utils.admin_user_manager import AdminUserManager

def test_validation_error():
    with pytest.raises(ValidationError):
        raise ValidationError("Invalid input")

def test_session_manager_create_and_get():
    manager = SessionManager()
    session = manager.create_session(user_id=1)
    assert manager.get_session(session.session_id) == session

def test_user_session_expiry():
    session = UserSession(user_id=1, ttl=1)
    import time
    time.sleep(2)
    assert session.is_expired()

def test_admin_user_manager_add_and_get():
    manager = AdminUserManager()
    manager.add_user("admin", "password")
    user = manager.get_user("admin")
    assert user is not None
    assert user.username == "admin"