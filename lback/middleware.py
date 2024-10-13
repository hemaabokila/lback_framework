class MiddlewareManager:
    def __init__(self):
        self.middlewares = []

    def add_middleware(self, middleware):
        self.middlewares.append(middleware)

    def process_request(self, request):
        for middleware in self.middlewares:
            response = middleware.process_request(request)
            if response:  
                return response
        return None 

    def process_response(self, request, response):
        for middleware in reversed(self.middlewares):
            response = middleware.process_response(request, response)
        return response
