class AppController:

    def __init__(self, middleware_manager, router):

        self.middleware_manager = middleware_manager
        self.router = router

    def handle_request(self, request):
        middleware_response = self.middleware_manager.process_request(request)
    
        if middleware_response:
            return middleware_response
        response = self.router.handle_request(request)
        return response

    def add_middleware(self, middleware):

        self.middleware_manager.add_middleware(middleware)

    def add_route(self, path, view, methods=None):

        self.router.add_route(path, view, methods)

    def set_error_handler(self, handler):

        self.router.set_error_handler(handler)

    def run(self, host='localhost', port=8000):
    
        print(f"Running server on {host}:{port}")
