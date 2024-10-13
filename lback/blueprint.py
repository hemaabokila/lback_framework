class Blueprint:
    def __init__(self, name):
        self.name = name
        self.routes = []  
        self.middleware = []  
    def add_route(self, path, view, methods=['GET']):
   
        self.routes.append({
            'path': path,
            'view': view,
            'methods': methods
        })

    def register_middleware(self, middleware):
        self.middleware.append(middleware)

    def get_routes(self):
        return self.routes

    def __str__(self):
        return f"Blueprint(name={self.name}, routes={self.routes})"
