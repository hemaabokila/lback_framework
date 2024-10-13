import unittest
from lback.router import Route

class TestRouter(unittest.TestCase):
    
    def setUp(self):
        self.test_view = lambda request: {"status_code": 200, "body": "Test passed"}
        self.route = Route(path="/test", view=self.test_view, methods=['GET'])

    def test_handle_request(self):
        request = type('Request', (), {"path": "/test", "method": "GET"})
        response = self.route.handle_request(request)
        self.assertEqual(response['status_code'], 200)
        self.assertEqual(response['body'], "Test passed")

    def test_method_not_allowed(self):
        request = type('Request', (), {"path": "/test", "method": "POST"})
        response = self.route.handle_request(request)
        self.assertEqual(response['status_code'], 405)
        self.assertEqual(response['body'], "Method Not Allowed")

    def test_route_not_found(self):
        request = type('Request', (), {"path": "/nonexistent", "method": "GET"})
        response = self.route.handle_request(request)
        self.assertEqual(response['status_code'], 404)
        self.assertEqual(response['body'], "Not Found")

    def test_route_with_variable(self):
        self.route = Route(path="/test/<id>", view=self.test_view, methods=['GET'])
        request = type('Request', (), {"path": "/test/123", "method": "GET"})
        response = self.route.handle_request(request)
        self.assertEqual(response['status_code'], 200)
        self.assertEqual(response['body'], "Test passed")
        self.assertEqual(request.params, {'id': '123'})  
if __name__ == '__main__':
    unittest.main()
