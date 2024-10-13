import unittest
from unittest.mock import patch, MagicMock
from lback.auth import AuthMiddleware
from datetime import *

class TestAuthMiddleware(unittest.TestCase):

    def setUp(self):
        self.middleware = AuthMiddleware()

    @patch('lback.auth.Session')
    @patch('lback.auth.User')
    def test_process_request_valid_token(self, mock_user, mock_session):
        mock_request = MagicMock()
        mock_request.headers = {'Authorization': 'Bearer valid_token'}
        mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_user.token_expiry = datetime.utcnow() + timedelta(hours=1)
        response = self.middleware.process_request(mock_request)
        self.assertIsNone(response) 
    @patch('lback.auth.Session')
    @patch('lback.auth.User')
    
    def test_process_request_invalid_token(self, mock_user, mock_session):
        mock_request = MagicMock()
        mock_request.headers = {'Authorization': 'Bearer invalid_token'}
        mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None
        response = self.middleware.process_request(mock_request)
        self.assertEqual(response['status_code'], 403)

    def test_process_request_no_auth_header(self):
        mock_request = MagicMock()
        mock_request.headers = {}
        response = self.middleware.process_request(mock_request)
        self.assertEqual(response['status_code'], 401)

    def test_process_request_invalid_header_format(self):
        mock_request = MagicMock()
        mock_request.headers = {'Authorization': 'InvalidFormat'}
        response = self.middleware.process_request(mock_request)
        self.assertEqual(response['status_code'], 401) 
if __name__ == '__main__':
    unittest.main()
