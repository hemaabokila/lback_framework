import json
import logging
import http
import re
from typing import Any, Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)

class Response:
    def __init__(self, body: Any = None, status_code: int = 200, headers: Optional[Dict[str, str]] = None, content_type: Optional[str] = None):
        self.body = body
        self.status_code = status_code
        self.headers: Dict[str, str] = headers if headers is not None else {}

        if content_type is not None and "Content-Type" not in self.headers:
             self.headers["Content-Type"] = content_type

        logger.debug(f"Response initialized with status: {self.status_code}, body type: {type(self.body).__name__}, headers: {self.headers}")

    def get_wsgi_response(self) -> Tuple[str, List[Tuple[str, str]], List[bytes]]:
        try:
            status_text = http.HTTPStatus(self.status_code).phrase
        except ValueError:
            status_text = "Unknown Status"
        status_line = f"{self.status_code} {status_text}"

        header_list = [(key, value) for key, value in self.headers.items()]

        body_bytes = b''
        if self.body is None:
            body_bytes = b''
        elif isinstance(self.body, bytes):
            body_bytes = self.body
        elif isinstance(self.body, str):
            try:
                encoding = self._get_encoding()
                body_bytes = self.body.encode(encoding)
            except Exception as e:
                logger.error(f"Failed to encode response body: {e}", exc_info=True)
                body_bytes = b'Error encoding response body'
                status_line = "500 Internal Server Error"
                header_list = [("Content-Type", "text/plain")]
                self.status_code = 500
        else:
            logger.warning(f"Unsupported response body type: {type(self.body).__name__}. Converting to string.")
            try:
                encoding = self._get_encoding()
                body_bytes = str(self.body).encode(encoding)
            except Exception as e:
                 logger.error(f"Failed to convert and encode unsupported body type: {e}", exc_info=True)
                 body_bytes = b'Error processing response body'
                 status_line = "500 Internal Server Error"
                 header_list = [("Content-Type", "text/plain")]
                 self.status_code = 500

        if "Content-Length" not in self.headers and body_bytes is not None:
             self.headers["Content-Length"] = str(len(body_bytes))
             header_list = [(key, value) for key, value in self.headers.items()]

        logger.debug(f"Prepared WSGI response: Status='{status_line}', Headers={header_list}, Body length={len(body_bytes)}")
        return status_line, header_list, [body_bytes]

    def _get_encoding(self) -> str:
        content_type = self.headers.get("Content-Type")
        if content_type:
            charset_match = re.search(r'charset=([^;]+)', content_type)
            if charset_match:
                return charset_match.group(1).strip()
        return 'utf-8'

    @staticmethod
    def json(data: Any = None, status_code: int = http.HTTPStatus.OK.value, headers: Optional[Dict[str, str]] = None, message: Optional[str] = None) -> 'JSONResponse':
         return JSONResponse(data=data, status_code=status_code, headers=headers, message=message)

    @staticmethod
    def html(content: str, status_code: int = http.HTTPStatus.OK.value, headers: Optional[Dict[str, str]] = None) -> 'HTMLResponse':
         return HTMLResponse(content=content, status_code=status_code, headers=headers)

    @staticmethod
    def redirect(redirect_url: str, status_code: int = http.HTTPStatus.FOUND.value, headers: Optional[Dict[str, str]] = None) -> 'RedirectResponse':
         return RedirectResponse(redirect_url=redirect_url, status_code=status_code, headers=headers)

    @staticmethod
    def error(message: str = "Internal Server Error", status_code: int = http.HTTPStatus.INTERNAL_SERVER_ERROR.value) -> 'JSONResponse':
         return JSONResponse(data={"error": message}, status_code=status_code)

    @staticmethod
    def not_found(message: str = "Not Found") -> 'JSONResponse':
         return JSONResponse(data={"error": message}, status_code=http.HTTPStatus.NOT_FOUND.value)

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> 'JSONResponse':
         return JSONResponse(data={"error": message}, status_code=http.HTTPStatus.UNAUTHORIZED.value)

    @staticmethod
    def bad_request(message: str = "Bad Request") -> 'JSONResponse':
         return JSONResponse(data={"error": message}, status_code=http.HTTPStatus.BAD_REQUEST.value)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> 'JSONResponse':
         return JSONResponse(data={"error": message}, status_code=http.HTTPStatus.FORBIDDEN.value)

    @staticmethod
    def conflict(message: str = "Conflict") -> 'JSONResponse':
         return JSONResponse(data={"error": message}, status_code=http.HTTPStatus.CONFLICT.value)


class JSONResponse(Response):
    def __init__(self, data: Any = None, status_code: int = 200, headers: Optional[Dict[str, str]] = None, message: Optional[str] = None):
        body_data = {"data": data}
        if message is not None:
             body_data["message"] = message

        try:
            json_body_string = json.dumps(body_data, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to serialize JSON response body: {e}", exc_info=True)
            json_body_string = json.dumps({"error": "Internal Server Error", "message": "Failed to serialize response data"}, ensure_ascii=False)
            status_code = 500
            message = "Internal Server Error"

        super().__init__(
            body=json_body_string,
            status_code=status_code,
            headers=headers,
            content_type="application/json; charset=utf-8"
        )
        logger.debug(f"JSONResponse created with status {self.status_code}.")

class HTMLResponse(Response):
    def __init__(self, content: str, status_code: int = 200, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            body=content,
            status_code=status_code,
            headers=headers,
            content_type="text/html; charset=utf-8"
        )
        logger.debug(f"HTMLResponse created with status {self.status_code}.")

class RedirectResponse(Response):
    def __init__(self, redirect_url: str, status_code: int = 302, headers: Optional[Dict[str, str]] = None):
        redirect_headers = headers if headers is not None else {}
        redirect_headers["Location"] = redirect_url

        if not (300 <= status_code < 400):
            logger.warning(f"RedirectResponse created with non-redirect status code: {status_code}. Using 302 instead.")
            status_code = 302

        super().__init__(
            body=b'',
            status_code=status_code,
            headers=redirect_headers,
            content_type="text/plain"
        )
        logger.debug(f"RedirectResponse created to URL: {redirect_url} with status {self.status_code}.")