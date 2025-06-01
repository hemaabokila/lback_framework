from lback.api.view import APIView
from lback.core.response import Response
from lback.core.router import Router

class HelloView(APIView):
    def get(self, request):
        return Response({"message": "hello"})

def test_api_response():
    resp = Response({"foo": "bar"}, status=200)
    assert resp.data == {"foo": "bar"}
    assert resp.status == 200


def test_api_router_register_and_route():
    router = Router()
    view = HelloView()
    router.register("/hello", view)

    class DummyRequest:
        method = "GET"
    response = router.handle_request("/hello", DummyRequest())
    assert isinstance(response, Response)
    assert response.data == {"message": "hello"}