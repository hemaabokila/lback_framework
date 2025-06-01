import logging
import json
import urllib.parse
from typing import Optional,Any
from http import HTTPStatus
import enum
from werkzeug.datastructures import FileStorage, MultiDict 
from werkzeug.formparser import parse_form_data

from lback.core.base_middleware import BaseMiddleware
from lback.core.response import Response
from lback.core.types import Request, UploadedFile 

logger = logging.getLogger(__name__)

class BodyParsingMiddleware(BaseMiddleware):
    """
    Middleware for parsing the request body based on Content-Type.
    Handles application/json, application/x-www-form-urlencoded, and multipart/form-data (using Werkzeug).
    Attaches parsed data to request.parsed_body (MultiDict) and uploaded files to request.files (dict of UploadedFile or list of UploadedFile).
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize BodyParsingMiddleware."""
        self.config = config
        logger.info("BodyParsingMiddleware initialized (using Werkzeug).")

    def process_request(self, request: Request) -> Optional[Response]:
        """
        Parses the request body based on Content-Type.
        Fills request.parsed_body and request.files.
        Returns None to continue middleware chain, or a Response in case of error.
        """
        content_type = request.headers.get('CONTENT-TYPE', '').lower()
        request_method_str = request.method.value if isinstance(request.method, enum.Enum) else request.method

        request.parsed_body = MultiDict()
        request.files = MultiDict()

        if request_method_str not in ['POST', 'PUT', 'PATCH']:
            return None

        try:
            if 'application/json' in content_type:
                body_bytes = request.body_bytes
                if body_bytes:
                    try:
                        body_text = body_bytes.decode('utf-8')
                        request.parsed_body = json.loads(body_text)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON body received for {request_method_str} {request.path}.")
                        return Response(HTTPStatus.BAD_REQUEST.value, "Invalid JSON body")
                    except Exception as e:
                        logger.error(f"Unexpected error parsing JSON body: {e}", exc_info=True)
                        return Response(HTTPStatus.INTERNAL_SERVER_ERROR.value, "Error parsing JSON body")

            elif 'application/x-www-form-urlencoded' in content_type:
                body_text = request.body_text
                if body_text:
                    try:
                        parsed_data_qs = urllib.parse.parse_qs(body_text)
                        request.parsed_body = MultiDict(parsed_data_qs)
                    except Exception as e:
                        logger.error(f"Error parsing form-urlencoded body: {e}", exc_info=True)
                        return Response(HTTPStatus.BAD_REQUEST.value, "Invalid form-urlencoded body")

            elif 'multipart/form-data' in content_type:
                content_length_str = request.headers.get('CONTENT-LENGTH')
                content_length = 0
                if content_length_str and content_length_str.isdigit():
                    try:
                        content_length = int(content_length_str)
                    except ValueError:
                        logger.warning(f"Invalid Content-Length '{content_length_str}' for {request_method_str} {request.path}. Treating as 0.")
                        content_length = 0

                if content_length != 0:
                    try:
                        _, form_data_werkzeug, files_data_werkzeug = parse_form_data(request.environ)
                        request.parsed_body = form_data_werkzeug
                        uploaded_files_processed: MultiDict = MultiDict()
                        if files_data_werkzeug:
                            for field_name, file_storage_list_or_single in files_data_werkzeug.items(multi=True):
                                if isinstance(file_storage_list_or_single, FileStorage):
                                    uploaded_file = UploadedFile(
                                        filename=file_storage_list_or_single.filename,
                                        content_type=file_storage_list_or_single.mimetype,
                                        file=file_storage_list_or_single.stream,
                                        field_name=field_name,
                                        size=file_storage_list_or_single.content_length or 0,
                                        headers=dict(file_storage_list_or_single.headers)
                                    )
                                    uploaded_files_processed.add(field_name, uploaded_file)
                        request.files = uploaded_files_processed
                    except Exception as e:
                        logger.error(f"Exception during multipart parsing: {e}", exc_info=True)
                        request.parsed_body = MultiDict()
                        request.files = MultiDict()
                        error_message = f"Error parsing multipart body with Werkzeug: {e}"
                        return Response(body=error_message.encode('utf-8'), status_code=HTTPStatus.BAD_REQUEST.value, content_type="text/plain")
        except Exception as e:
            logger.error(f"Unhandled exception during body parsing for {request_method_str} {request.path}: {e}", exc_info=True)
            request.parsed_body = MultiDict()
            request.files = MultiDict()
            error_message = f"Internal Server Error during body parsing: {e}"
            return Response(body=error_message.encode('utf-8'), status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, content_type="text/plain")

        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """
        Processes the outgoing response.
        Cleans up any temporary files created during multipart body parsing (Werkzeug).
        """
        if request.files:
            for field_name, file_info in request.files.items():
                if isinstance(file_info, list):
                    for uploaded_file in file_info:
                        if isinstance(uploaded_file, UploadedFile) and hasattr(uploaded_file, 'close') and callable(uploaded_file.close):
                            try:
                                uploaded_file.close()
                            except Exception as e:
                                logger.error(f"Error closing uploaded file for field '{field_name}', filename '{uploaded_file.filename}': {e}", exc_info=True)
                elif isinstance(file_info, UploadedFile):
                    if hasattr(file_info, 'close') and callable(file_info.close):
                        try:
                            file_info.close()
                        except Exception as e:
                            logger.error(f"Error closing uploaded file for field '{field_name}', filename '{file_info.filename}': {e}", exc_info=True)
        return response

