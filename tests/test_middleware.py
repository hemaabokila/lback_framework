import unittest
from lback.middleware import MiddlewareManager
from lback.auth import AuthMiddleware
from lback.debug import DebugMiddleware

class TestMiddleware(unittest.TestCase):
    def setUp(self):
        self.middleware_manager = MiddlewareManager()

    def test_auth_middleware_authorized(self):
        auth_middleware = AuthMiddleware()
        self.middleware_manager.add_middleware(auth_middleware)
        request = type('Request', (), {"headers": {"Authorization": "Bearer token"}})
        response = self.middleware_manager.process_request(request)
        self.assertIsNone(response)

    def test_auth_middleware_unauthorized(self):
        auth_middleware = AuthMiddleware()
        self.middleware_manager.add_middleware(auth_middleware)
        request = type('Request', (), {"headers": {}})
        response = self.middleware_manager.process_request(request)
        self.assertEqual(response['status_code'], 401)
        self.assertEqual(response['body'], "Unauthorized")

    def test_debug_middleware(self):
        debug_middleware = DebugMiddleware()
        self.middleware_manager.add_middleware(debug_middleware)
        request = type('Request', (), {"path": "/test", "method": "GET"})
        response = self.middleware_manager.process_request(request)
        self.assertIsNone(response)

    def test_debug_middleware_response_logging(self):
        debug_middleware = DebugMiddleware()
        self.middleware_manager.add_middleware(debug_middleware)
        request = type('Request', (), {"path": "/test", "method": "GET"})
        response = {"status_code": 200, "body": "OK"}
        processed_response = self.middleware_manager.process_response(request, response)
        self.assertEqual(processed_response, response)

if __name__ == '__main__':
    unittest.main()
