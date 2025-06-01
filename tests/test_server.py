from lback.core.server import Server

def setup_function():
    global server
    server = Server()

def test_add_route():
    server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
    assert len(server.routes) == 1

def test_handle_request():
    server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
    request = type('Request', (), {"path": "/", "method": "GET"})
    response = server.handle_request(request)
    assert response['status_code'] == 200
    assert response['body'] == "Hello"

def test_handle_request_not_found():
    request = type('Request', (), {"path": "/notfound", "method": "GET"})
    response = server.handle_request(request)
    assert response['status_code'] == 404
    assert response['body'] == "Not Found"

def test_method_not_allowed():
    server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"}, methods=['POST'])
    request = type('Request', (), {"path": "/", "method": "GET"})
    response = server.handle_request(request)
    assert response['status_code'] == 405
    assert response['body'] == "Method Not Allowed"

def test_add_multiple_routes():
    server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
    server.add_route("/about", lambda request: {"status_code": 200, "body": "About Page"})
    assert len(server.routes) == 2

def test_handle_multiple_routes():
    server.add_route("/", lambda request: {"status_code": 200, "body": "Hello"})
    server.add_route("/about", lambda request: {"status_code": 200, "body": "About Page"})
    
    request_home = type('Request', (), {"path": "/", "method": "GET"})
    response_home = server.handle_request(request_home)
    assert response_home['status_code'] == 200
    assert response_home['body'] == "Hello"
    
    request_about = type('Request', (), {"path": "/about", "method": "GET"})
    response_about = server.handle_request(request_about)
    assert response_about['status_code'] == 200
    assert response_about['body'] == "About Page"