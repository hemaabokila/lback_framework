from lback.core.router import Route

def setup_function():
    global test_view, route
    test_view = lambda request: {"status_code": 200, "body": "Test passed"}
    route = Route(path="/test", view=test_view, methods=['GET'])

def test_handle_request():
    request = type('Request', (), {"path": "/test", "method": "GET"})
    response = route.handle_request(request)
    assert response['status_code'] == 200
    assert response['body'] == "Test passed"

def test_method_not_allowed():
    request = type('Request', (), {"path": "/test", "method": "POST"})
    response = route.handle_request(request)
    assert response['status_code'] == 405
    assert response['body'] == "Method Not Allowed"

def test_route_not_found():
    request = type('Request', (), {"path": "/nonexistent", "method": "GET"})
    response = route.handle_request(request)
    assert response['status_code'] == 404
    assert response['body'] == "Not Found"

def test_route_with_variable():
    route_with_var = Route(path="/test/<id>", view=test_view, methods=['GET'])
    request = type('Request', (), {"path": "/test/123", "method": "GET"})
    response = route_with_var.handle_request(request)
    assert response['status_code'] == 200
    assert response['body'] == "Test passed"
    assert hasattr(request, "params")
    assert request.params == {'id': '123'}