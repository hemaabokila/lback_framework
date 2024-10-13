import unittest
from lback.server import Server

class TestServer(unittest.TestCase):

    def setUp(self):
        self.server = Server()

    def test_add_route(self):
        self.server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
        self.assertEqual(len(self.server.routes), 1)

    def test_handle_request(self):
        self.server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
        request = type('Request', (), {"path": "/", "method": "GET"})
        response = self.server.handle_request(request)
        self.assertEqual(response['status_code'], 200)
        self.assertEqual(response['body'], "Hello")

    def test_handle_request_not_found(self):
        request = type('Request', (), {"path": "/notfound", "method": "GET"})
        response = self.server.handle_request(request)
        self.assertEqual(response['status_code'], 404)
        self.assertEqual(response['body'], "Not Found")

    def test_method_not_allowed(self):
        self.server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"}, methods=['POST'])
        request = type('Request', (), {"path": "/", "method": "GET"})
        response = self.server.handle_request(request)
        self.assertEqual(response['status_code'], 405)
        self.assertEqual(response['body'], "Method Not Allowed")

    def test_add_multiple_routes(self):
        self.server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
        self.server.add_route("/about", lambda request: {"status_code": 200, "body": "About Page"})
        self.assertEqual(len(self.server.routes), 2)

    def test_handle_multiple_routes(self):
        self.server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
        self.server.add_route("/about", lambda request: {"status_code": 200, "body": "About Page"})
        
        request_home = type('Request', (), {"path": "/", "method": "GET"})
        response_home = self.server.handle_request(request_home)
        self.assertEqual(response_home['status_code'], 200)
        self.assertEqual(response_home['body'], "Hello")
        
        request_about = type('Request', (), {"path": "/about", "method": "GET"})
        response_about = self.server.handle_request(request_about)
        self.assertEqual(response_about['status_code'], 200)
        self.assertEqual(response_about['body'], "About Page")

if __name__ == '__main__':
    unittest.main()
