import os
import mimetypes
import logging

from lback.core.response import Response
from lback.core.base_middleware import BaseMiddleware

logger = logging.getLogger(__name__)

class StaticFilesMiddleware(BaseMiddleware):
    """
    Middleware to serve static files during development.
    Only active when config.DEBUG is True.
    """

    def process_request(self, request):
        """
        Processes the incoming request to check if it's for a static file.
        If it is and the file exists, serves the file directly.

        Args:
            request: The incoming request object. Expected to have 'path' and 'config' attributes.

        Returns:
            A Response object if a static file is served, otherwise None
            to pass the request to the next middleware.
        """
  
        config = getattr(request, 'config', None)
        if config is None or not getattr(config, 'DEBUG', False):
            logger.debug("StaticFilesMiddleware skipped: DEBUG is not True or config is missing.")
            return None

        static_url = getattr(config, 'STATIC_URL', '/static/')
        static_root = getattr(config, 'STATIC_ROOT', 'static')

        if not static_url.endswith('/'):
            static_url += '/'

        if request.path.startswith(static_url):
            relative_static_path = request.path[len(static_url):]
            logger.debug(f"Attempting to serve static file: {relative_static_path}")
            static_file_path = os.path.join(static_root, relative_static_path)

            abs_static_root = os.path.abspath(static_root)
            abs_static_file_path = os.path.abspath(static_file_path)

            if not abs_static_file_path.startswith(abs_static_root):
                 logger.warning(f"Attempted directory traversal detected: {request.path}")
                 return None

            if os.path.exists(abs_static_file_path) and os.path.isfile(abs_static_file_path):
                try:
                    mime_type, _ = mimetypes.guess_type(abs_static_file_path)
                    if mime_type is None:
                        mime_type = 'application/octet-stream'

                    with open(abs_static_file_path, 'rb') as f:
                        file_content = f.read()

                    logger.info(f"Served static file: {abs_static_file_path}")

                    return Response(file_content, status_code=200, headers={'Content-Type': mime_type})

                except IOError as e:
                    logger.error(f"Error reading static file {abs_static_file_path}: {e}", exc_info=True)
                    return None 

            else:
                logger.debug(f"Static file not found or is not a file: {abs_static_file_path}")
                return None

        logger.debug(f"Request path '{request.path}' does not match STATIC_URL '{static_url}'.")
        return None

    def process_response(self, request, response):
        """
        Processes the outgoing response.

        Args:
            request: The incoming request object.
            response: The outgoing response object.

        Returns:
            The response object.
        """
        logger.debug("StaticFilesMiddleware process_response called.")
        return response
