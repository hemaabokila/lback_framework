from lback.router import Route
from lback.middleware import MiddlewareManager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Dict, Callable


class Server:
    def __init__(self):
        self.routes: List[Route] = []
        self.middleware_manager = MiddlewareManager()

    def add_route(self, path: str, view: Callable, methods: List[str] = ['GET']) -> None:
        route = Route(path, view, methods)
        self.routes.append(route)

    def handle_request(self, request: Dict[str, any]) -> Dict[str, any]:
        for route in self.routes:
            if request['path'] == route.path and request['method'] in route.methods:
                response = route.handle_request(request)
                return self.middleware_manager.process_response(request, response)
        
        return {"status_code": 404, "body": "Not Found"}

    def start(self) -> None:
        print("Server is running on http://127.0.0.1:8000...")
        
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.handle_request("GET")
                
            def do_POST(self):
                self.handle_request("POST")

            def handle_request(self, method: str) -> None:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
                
                request = {
                    'path': self.path,
                    'method': method,
                    'body': body,
                    'headers': dict(self.headers)
                }
                
                response = self.server.handle_request(request)
                
                self.send_response(response['status_code'])
                self.end_headers()
                self.wfile.write(response['body'].encode('utf-8'))

        server_address = ('', 8000)
        httpd = HTTPServer(server_address, RequestHandler)
        httpd.handle_request = self.handle_request
        httpd.serve_forever()

