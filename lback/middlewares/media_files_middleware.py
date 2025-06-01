import os
import mimetypes
import logging

from lback.core.response import Response
from lback.core.base_middleware import BaseMiddleware

logger = logging.getLogger(__name__)

class MediaFilesMiddleware(BaseMiddleware):
    """
    Middleware to serve user-uploaded media files during development.
    Only active when config.DEBUG is True.
    It uses UPLOAD_URL and UPLOAD_FOLDER from the application's configuration.
    """

    def process_request(self, request):
        """
        Processes the incoming request to check if it's for a media file.
        If it is and the file exists, serves the file directly.

        Args:
            request: The incoming request object. Expected to have 'path' and 'config' attributes.

        Returns:
            A Response object if a media file is served, otherwise None
            to pass the request to the next middleware.
        """
        
        config = getattr(request, 'config', None)
        if config is None or not getattr(config, 'DEBUG', False):
            logger.debug("MediaFilesMiddleware skipped: DEBUG is not True or config is missing.")
            return None

        upload_url = getattr(config, 'UPLOAD_URL', '/media/uploads/')
        upload_folder_relative = getattr(config, 'UPLOAD_FOLDER', 'media/uploads')
        base_dir = getattr(config, 'BASE_DIR', os.getcwd())
        upload_root = os.path.join(base_dir, upload_folder_relative)

        if not upload_url.endswith('/'):
            upload_url += '/'


        if request.path.startswith(upload_url):
            relative_media_path = request.path[len(upload_url):]
            logger.debug(f"Attempting to serve media file: {relative_media_path}")
            media_file_path = os.path.join(upload_root, relative_media_path)

            abs_upload_root = os.path.abspath(upload_root)
            abs_media_file_path = os.path.abspath(media_file_path)

            if not abs_media_file_path.startswith(abs_upload_root):
                logger.warning(f"Attempted directory traversal detected for media file: {request.path}")
                return None 

            if os.path.exists(abs_media_file_path) and os.path.isfile(abs_media_file_path):
                try:

                    mime_type, _ = mimetypes.guess_type(abs_media_file_path)
                    if mime_type is None:
                        mime_type = 'application/octet-stream'

                    with open(abs_media_file_path, 'rb') as f:
                        file_content = f.read()

                    logger.info(f"Served media file: {abs_media_file_path}")

                    return Response(file_content, status_code=200, headers={'Content-Type': mime_type})

                except IOError as e:
                    logger.error(f"Error reading media file {abs_media_file_path}: {e}", exc_info=True)
                    return None

            else:
                logger.debug(f"Media file not found or is not a file: {abs_media_file_path}")
                return None 

        logger.debug(f"Request path '{request.path}' does not match UPLOAD_URL '{upload_url}'.")
        return None

    def process_response(self, request, response):
        """
        Processes the outgoing response. For media files, this middleware usually
        returns a response directly, so this method might not be called for served files.
        It's included for consistency with BaseMiddleware.

        Args:
            request: The incoming request object.
            response: The outgoing response object.

        Returns:
            The response object.
        """
        logger.debug("MediaFilesMiddleware process_response called.")
        return response

