import pytest
from unittest.mock import patch, MagicMock
from lback.middlewares.auth_midlewares import AuthMiddleware
from datetime import datetime, timedelta

@pytest.fixture
def middleware():
    return AuthMiddleware()

@patch('auth.Session')
@patch('auth.User')
def test_process_request_valid_token(mock_user, mock_session, middleware):
    mock_request = MagicMock()
    mock_request.headers = {'Authorization': 'Bearer valid_token'}
    mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_user
    mock_user.token_expiry = datetime.utcnow() + timedelta(hours=1)
    response = middleware.process_request(mock_request)
    assert response is None

@patch('auth.Session')
@patch('auth.User')
def test_process_request_invalid_token(mock_user, mock_session, middleware):
    mock_request = MagicMock()
    mock_request.headers = {'Authorization': 'Bearer invalid_token'}
    mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None
    response = middleware.process_request(mock_request)
    assert response['status_code'] == 403

def test_process_request_no_auth_header(middleware):
    mock_request = MagicMock()
    mock_request.headers = {}
    response = middleware.process_request(mock_request)
    assert response['status_code'] == 401

def test_process_request_invalid_header_format(middleware):
    mock_request = MagicMock()
    mock_request.headers = {'Authorization': 'InvalidFormat'}
    response = middleware.process_request(mock_request)
    assert response['status_code'] == 401