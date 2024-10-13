import re
from typing import Callable, List, Dict, Any
import logging

class Route:
    def __init__(self, path: str, view: Callable, methods: List[str] = ['GET']) -> None:
        self.path = path
        self.view = view
        self.methods = methods
        self.regex = self.path_to_regex(path)

    def path_to_regex(self, path: str) -> re.Pattern:
        path = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
        return re.compile(f"^{path}$")

    def handle_request(self, request: Any) -> Dict[str, Any]:
        if request.method not in self.methods:
            return {"status_code": 405, "body": "Method Not Allowed"}

        match = self.regex.match(request.path)
        if not match:
            return {"status_code": 404, "body": "Not Found"}

        request_params = match.groupdict()
        request.params = request_params

        try:
            return self.view(request)
        except Exception as e:
            logging.error(f"Error in view execution: {str(e)}")
            return {"status_code": 500, "body": f"Internal Server Error"}

    def __repr__(self) -> str:
        return f"Route(path='{self.path}', methods={self.methods})"
