import logging
from lback.core.base_middleware import BaseMiddleware

logger = logging.getLogger(__name__)

class CORSMiddleware(BaseMiddleware):
    def __init__(self, allowed_origins=None):
        """
        Initialize the CORS middleware.

        Args:
            allowed_origins (list): A list of allowed origins. Use ['*'] to allow all origins.
        """
        self.allowed_origins = allowed_origins or ["*"]

    def process_request(self, request):
        """
        Process the incoming request to handle preflight (OPTIONS) requests.
        """
        if request.method == "OPTIONS":
            response = {
                "status_code": 204,
                "headers": self._get_cors_headers(request)
            }
            return response
        return None

    def process_response(self, request, response):
        """
        Process the outgoing response to add CORS headers.
        """
        cors_headers = self._get_cors_headers(request)
        response.headers.update(cors_headers)
        return response

    def _get_cors_headers(self, request):
        """
        Generate CORS headers based on the request and allowed origins.
        """
        origin = request.headers.get("Origin", "")
        if "*" in self.allowed_origins or origin in self.allowed_origins:
            return {
                "Access-Control-Allow-Origin": origin if origin else "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Credentials": "true"
            }
        return {}
