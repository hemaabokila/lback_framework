from typing import Dict, Any, Optional, Union, List, BinaryIO
from urllib.parse import parse_qs, urlparse
import logging
import enum
from http.cookies import SimpleCookie 
import os
from sqlalchemy.orm import Session as SQLASession

from lback.core.config import Config
from lback.core.templates import TemplateRenderer
from lback.core.error_handler import ErrorHandler
from lback.core.signals import SignalDispatcher
try:
    from lback.utils.app_session import AppSession
except ImportError:
    class AppSession:
        pass

logger = logging.getLogger(__name__)

class UploadedFile:
    def __init__(self, filename: str, content_type: str, file: BinaryIO, field_name: str, size: int, headers: Dict[str, str] = None):
        """
        Represents a single uploaded file from a multipart/form-data request.

        Args:
            filename: The name of the uploaded file.
            content_type: The content type of the file (e.g., 'image/png').
            file: A file-like object containing the file content.
            field_name: The name of the form field that contained this file.
            size: The size of the file in bytes.
            headers: Optional dictionary of headers specific to the file part (e.g., Content-Disposition).
        """
        self.filename = filename
        self.content_type = content_type
        self.file = file 
        self.field_name = field_name
        self.size = size
        self.headers = headers if headers is not None else {}

    def read(self, size=-1):
        """Reads bytes from the file-like object."""
        if self.file:
            return self.file.read(size)
        return b''

    def seek(self, offset, whence=0):
        """Changes the stream position."""
        if self.file:
            self.file.seek(offset, whence)

    def close(self):
        """Closes the underlying file-like object if it has a close method."""
        if self.file and hasattr(self.file, 'close') and callable(self.file.close):
            self.file.close()

    def __repr__(self):
        return (f"<UploadedFile: filename='{self.filename}', field_name='{self.field_name}', "
                f"size={self.size}, content_type='{self.content_type}'>")



class HTTPMethod(enum.Enum):
    """Represents standard HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

    def __str__(self) -> str:
        """Return the string representation of the HTTP method."""
        return self.value

    def __eq__(self, other: Any) -> bool:
        """Compare HTTPMethod with string or other HTTPMethod."""
        if isinstance(other, str):
            return self.value.upper() == other.upper()
        elif isinstance(other, HTTPMethod):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Make HTTPMethod hashable."""
        return hash(self.value)


class Request:
    """
    Represents an incoming HTTP request.
    This object carries all request information (path, method, headers, body, query params)
    and serves as a context object to pass data (user, session, db_session, path_params, dependencies)
    through the middleware chain and to the view.
    Includes enhancements for file uploads, cookies, META, etc., populated by middlewares.
    """
    def __init__(self, path: str, method: Union[str, HTTPMethod], body: Union[str, bytes, None], headers: Dict[str, str], environ: Dict[str, Any]):
        """
        Initializes a Request object with raw request data and WSGI environment.
        """
        if not isinstance(path, str):
             logger.error(f"Invalid path type during Request initialization: {type(path)}")
             raise TypeError("Request path must be a string.")
        if not isinstance(method, (str, HTTPMethod)):
             logger.error(f"Invalid method type during Request initialization: {type(method)}")
             raise TypeError("Request method must be a string or HTTPMethod enum.")
        if not isinstance(headers, dict):
             logger.error(f"Invalid headers type during Request initialization: {type(headers)}")
             raise TypeError("Request headers must be a dictionary.")
        if body is not None and not isinstance(body, (str, bytes)):
             logger.error(f"Invalid body type during Request initialization: {type(body)}")
             raise TypeError("Request body must be a string, bytes, or None.")
        if not isinstance(environ, dict):
            logger.error(f"Invalid environ type during Request initialization: {type(environ)}")
            raise TypeError("Request environ must be a dictionary.")

        self.raw_path: str = path
        if isinstance(method, str):
            try:
                self.method: HTTPMethod = HTTPMethod(method.upper())
            except ValueError:
                self.method: Union[str, HTTPMethod] = method.upper()
                logger.warning(f"Received unknown HTTP method: {method}")
        else:
            self.method: HTTPMethod = method

        self._initial_body: Union[str, bytes, None] = body
        self.headers: Dict[str, str] = {k.replace('_', '-').upper(): v for k, v in headers.items()}
        self._environ: Dict[str, Any] = environ

        self._context: Dict[str, Any] = {}
        self.path: str = ""
        self.query_params: Dict[str, Any] = {}
        self.cookies: Dict[str, str] = {}
        self.meta: Dict[str, Any] = {}

        self._parsed_body: Optional[Dict[str, Any]] = None
        self._files: Dict[str, Union[UploadedFile, List[UploadedFile]]] = {}
        self._user: Optional[Any] = None
        self._session: Optional[AppSession] = None
        self._db_session: Optional[Any] = None

        self._error_handler: Optional[ErrorHandler] = None
        self._config: Optional[Config] = None
        self._template_renderer: Optional[TemplateRenderer] = None
        self._router: Optional[Any] = None
        self._dispatcher: Optional[SignalDispatcher] = None
        self._admin_registry: Optional[Any] = None
        self._admin_user_manager: Optional[Any] = None
        self._session_manager: Optional[Any] = None
        self._user_manager: Optional[Any] = None
        self._path_params: Dict[str, Any] = {}
        self.route_requires_auth: bool = False

        self._parse_url()
        self._parse_cookies()
        self._populate_meta()

        logger.debug(f"Request object initialized for {self.method} {self.path}")
        logger.debug(f"Headers: {self.headers}")
        logger.debug(f"Query Params: {self.query_params}")
        logger.debug(f"Cookies: {self.cookies}")


    def _parse_url(self):
        """
        Parses the raw request path to extract the clean path and query parameters.
        Updates self.path and self.query_params.
        Called during __init__.
        """
        logger.debug(f"Parsing URL: {self.raw_path}")
        try:
            parsed_url = urlparse(self.raw_path)
            self.path: str = parsed_url.path 
            self.query_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed_url.query).items()}
            logger.debug(f"URL parsed. Clean path: {self.path}, Query params: {self.query_params}")
        except Exception as e:
            logger.error(f"Error parsing URL '{self.raw_path}': {e}")
            self.path = self.raw_path
            self.query_params = {}

    def _parse_cookies(self):
        """
        Parses the 'Cookie' header to extract cookie key-value pairs.
        Updates self.cookies.
        Called during __init__.
        """
        logger.debug("Parsing cookies from headers.")
        cookie_header = self.headers.get('COOKIE')
        self.cookies = {}
        if cookie_header:
            try:
                cookie_object = SimpleCookie()
                cookie_object.load(cookie_header)
                self.cookies = {key: morsel.value for key, morsel in cookie_object.items()}
                logger.debug(f"Parsed {len(self.cookies)} cookies.")
            except Exception as e:
                logger.error(f"Error parsing Cookie header '{cookie_header}': {e}", exc_info=True)
        else:
             logger.debug("No 'Cookie' header found.")

    def _populate_meta(self):
        """
        Populates the self.meta dictionary with relevant information from the WSGI environment.
        Mimics Django's request.META.
        Called during __init__.
        """
        logger.debug("Populating META data from environ.")
        self.meta = {}
        for key, value in self._environ.items():
            if isinstance(key, str) and key.isupper():
                 if not key.startswith('WSGI.') and key not in ['SERVER_SOFTWARE', 'GATEWAY_INTERFACE']:
                     self.meta[key] = value

        for key, value in self._environ.items():
            if key.startswith('HTTP_'):
                 header_name = key[len('HTTP_'):].replace('_', '-')
                 if header_name not in self.meta: 
                     self.meta[header_name] = value

        if 'CONTENT_TYPE' in self._environ:
             self.meta['CONTENT-TYPE'] = self._environ['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in self._environ:
             self.meta['CONTENT-LENGTH'] = self._environ['CONTENT_LENGTH']

        self.meta['REQUEST_METHOD'] = self.method.value if isinstance(self.method, HTTPMethod) else self.method
        self.meta['PATH_INFO'] = self.path
        self.meta['SCRIPT_NAME'] = self._environ.get('SCRIPT_NAME', '')
        self.meta['QUERY_STRING'] = urlparse(self.raw_path).query
        self.meta['SERVER_NAME'] = self._environ.get('SERVER_NAME', '')
        self.meta['SERVER_PORT'] = self._environ.get('SERVER_PORT', '')
        self.meta['REMOTE_ADDR'] = self._environ.get('REMOTE_ADDR', '')
        self.meta['REMOTE_HOST'] = self._environ.get('REMOTE_HOST', '')
        self.meta['SERVER_PROTOCOL'] = self._environ.get('SERVER_PROTOCOL', '')
        self.meta['wsgi.url_scheme'] = self._environ.get('wsgi.url_scheme', '')

        logger.debug(f"Populated META with {len(self.meta)} keys.")

    @property
    def body_bytes(self) -> bytes:
        """
        Returns the request body as bytes. Reads the body from the stream if not already read.
        Caches the result. Note: This reads the entire body into memory.
        Use get_body_stream() for streaming large request bodies *before* accessing this property.
        """

        if isinstance(self._initial_body, bytes):
             return self._initial_body

        if isinstance(self._initial_body, str):
             self._initial_body = self._initial_body.encode('utf-8')
             return self._initial_body

        if self._initial_body is None and 'wsgi.input' in self._environ:
            try:
                content_length_str = self._environ.get('CONTENT_LENGTH')
                content_length = 0
                if content_length_str is not None and content_length_str.isdigit():
                    content_length = int(content_length_str)

                if content_length > 0:
                    config = self.get_context('config')
                    max_body_size = getattr(config, 'MAX_REQUEST_BODY_SIZE', 10 * 1024 * 1024)
                    if content_length > max_body_size:
                         logger.warning(f"Request body too large ({content_length} bytes) for {self.method} {self.path}. Max allowed: {max_body_size}.")
                         self._initial_body = b''
                         return self._initial_body


                    from io import BytesIO
                    body_stream = self._environ['wsgi.input']
                    read_content = body_stream.read(content_length)
                    self._initial_body = read_content
                    logger.debug(f"Read {len(self._initial_body)} bytes from wsgi.input.")
                    return self._initial_body
                else:
                    self._initial_body = b''
                    return self._initial_body
            except (ValueError, TypeError):
                logger.warning(f"Invalid CONTENT_LENGTH in environ for {self.method} {self.path}.")
                self._initial_body = b''
                return self._initial_body
            except Exception as e:
                logger.error(f"Error reading body from wsgi.input for {self.method} {self.path}: {e}", exc_info=True)
                self._initial_body = b''
                return self._initial_body
        else:
            return b''


    @property
    def body_text(self) -> Optional[str]:
        """
        Returns the request body as text (UTF-8 decoded).
        Caches the result of decoding. Returns None if decoding fails or body is empty.
        """
        if hasattr(self, '_cached_body_text'):
             return self._cached_body_text

        body_bytes = self.body_bytes
        if body_bytes:
            try:
                decoded_text = body_bytes.decode('utf-8')
                self._cached_body_text = decoded_text
                return decoded_text
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode request body as utf-8 for {self.method} {self.path}. Body content might be binary.")
                self._cached_body_text = None
                return None
        else:
            self._cached_body_text = None
            return None


    def get_body_stream(self) -> Optional[BinaryIO]:
        """
        Returns the raw input stream from the WSGI environment ('wsgi.input').
        Useful for streaming large request bodies without loading into memory.
        Note: Reading from this stream consumes the data. If you read from the stream,
        subsequent access to request.body_bytes or request.body_text might be empty
        or incomplete unless the stream supports seeking.
        The stream is typically available only *before* the body_bytes property is accessed
        for the first time (as body_bytes reads the whole stream).
        """
        return self._environ.get('wsgi.input')


    @property
    def parsed_body(self) -> Optional[Dict[str, Any]]:
         """
         Provides access to parsed body data (from form-urlencoded or JSON).
         This data is expected to be populated by a Body Parsing Middleware.
         Returns a dictionary or None if no body or parsing failed.
         """
         return self._parsed_body

    @parsed_body.setter
    def parsed_body(self, data: Optional[Dict[str, Any]]):
        """Setter for parsed body data, used by middleware."""
        if data is not None and not isinstance(data, dict):
             logger.warning(f"Attempted to set non-dictionary parsed_body on {self.method} {self.path}: {type(data)}")
             self._parsed_body = None
        else:
             self._parsed_body = data
        logger.debug(f"Parsed body set: {type(self._parsed_body)}")


    @property
    def files(self) -> Dict[str, Union[UploadedFile, List[UploadedFile]]]:
         """
         Provides access to uploaded files (from multipart/form-data).
         This data is expected to be populated by a Body Parsing Middleware.
         Returns a dictionary where keys are form field names and values are UploadedFile
         objects or lists of UploadedFile objects for multiple files with the same name.
         Returns an empty dictionary if no files were uploaded or parsing failed.
         """
         return self._files

    @files.setter
    def files(self, files_dict: Dict[str, Union[UploadedFile, List[UploadedFile]]]):
        """Setter for uploaded files dictionary, used by middleware."""
        if not isinstance(files_dict, dict):
             logger.warning(f"Attempted to set non-dictionary files on {self.method} {self.path}: {type(files_dict)}")
             self._files = {}
        else:
             self._files = files_dict
        logger.debug(f"Files dictionary set with keys: {list(self._files.keys())}")

    @property
    def GET(self) -> Dict[str, Any]:
        """
        Provides access to parsed query parameters.
        Equivalent to request.query_params.
        """
        return self.query_params

    @property
    def POST(self) -> Dict[str, Any]:
        """
        Provides access to parsed body data typically from form submissions
        (application/x-www-form-urlencoded or multipart/form-data).
        This data is expected to be populated in request.parsed_body by a Body Parsing Middleware.
        Returns an empty dictionary if the method is not POST or no form data is available.
        """
        if self.method == HTTPMethod.POST:
             return self.parsed_body if isinstance(self.parsed_body, dict) else {}
        return {}

    @property
    def DATA(self) -> Dict[str, Any]:
        """
        Provides access to parsed body data, suitable for APIs accepting JSON
        or other structured data in the body (PUT, PATCH, POST).
        Assumes Body Parsing Middleware has populated request.parsed_body.
        Returns an empty dictionary if no parsed body data is available.
        """
        if self.method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]:
             return self.parsed_body if isinstance(self.parsed_body, dict) else {}
        return {}

    @property
    def get_host(self) -> str:
        """
        Returns the hostname for the request, looking at standard headers first,
        then falling back to WSGI environment variables.
        """
        host = self.headers.get('HOST')
        if host:
            return host

        x_forwarded_host = self.headers.get('X-FORWARDED-HOST')
        if x_forwarded_host:
             return x_forwarded_host.split(',')[0].strip()
        server_name = self._environ.get('SERVER_NAME', '')
        server_port = self._environ.get('SERVER_PORT', '')
        if server_name:
            scheme = self.is_secure 
            if server_port and server_port != ('80' if not scheme else '443'):
                return f"{server_name}:{server_port}"
            return server_name

        return ''


    @property
    def is_secure(self) -> bool:
        """
        Returns True if the request is secure (HTTPS), checking WSGI environment
        and common headers set by proxies.
        """
        if self._environ.get('wsgi.url_scheme') == 'https':
            return True
        if self.headers.get('X-FORWARDED-PROTO', '').lower() == 'https':
            return True
        if self.headers.get('X-SCHEME', '').lower() == 'https':
             return True
        if self._environ.get('HTTPS') == 'on':
             return True
        return False

    def build_absolute_uri(self, location: Optional[str] = None) -> str:
        """
        Builds an absolute URI for a given location or the current request path.
        Mimics Django's build_absolute_uri.

        Args:
            location: A path or URL string. If None, uses the current request path.
                      Can be a relative path, absolute path (starting with '/'),
                      or a full URL (with scheme and host).

        Returns:
            The built absolute URI as a string.
        """
        scheme = 'https' if self.is_secure else 'http'
        host = self.get_host
        if not host:
            host = self._environ.get('SERVER_NAME', 'localhost')
            port = self._environ.get('SERVER_PORT')
            if port and port != ('80' if not self.is_secure else '443'):
                 host = f"{host}:{port}"

        if location is None:
            path_with_query = self.raw_path
            if not path_with_query.startswith('/') and urlparse(path_with_query).scheme == '':
                 path_with_query = '/' + path_with_query
            uri = f"{scheme}://{host}{path_with_query}"
        else:
            parsed_location = urlparse(location)
            if parsed_location.scheme or parsed_location.netloc:
                uri = location
            else:
                base_path = os.path.dirname(self.path)
                if not base_path.endswith('/') and base_path != '':
                     base_path += '/'
                elif base_path == '':
                     base_path = '/'
                from urllib.parse import urljoin
                base_url_for_join = f"{scheme}://{host}{base_path}"
                uri = urljoin(base_url_for_join, location)

        return uri

    def set_context(self, **kwargs: Any):
        """
        Sets key-value pairs in the request context dictionary.
        Also updates dedicated internal attributes if setters are defined
        and the key matches a property name.
        Used by AppController and Middlewares to attach request-scoped data.
        """
        logger.debug(f"Setting context data for {self.method} {self.path}: {list(kwargs.keys())}")
        for key, value in kwargs.items():
            if hasattr(type(self), key) and isinstance(getattr(type(self), key), property) and getattr(type(self), key).fset is not None:
                try:
                    setattr(self, key, value)
                    logger.debug(f"Set context key '{key}' using dedicated setter.")
                except Exception as e:
                    logger.warning(f"Error using setter for context key '{key}': {e}. Falling back to storing in _context dictionary.", exc_info=True)
                    self._context[key] = value
            else:
                self._context[key] = value

    def add_context(self, key: str, value: Any):
        """Adds a single key-value pair to the request context dictionary (alias for set_context)."""
        logger.debug(f"Adding context data for {self.method} {self.path}: {key}")
        self.set_context(**{key: value})


    def get_context(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieves a value from the internal context dictionary (_context).
        Known context items with dedicated properties should be accessed via those properties
        (e.g., request.db_session, request.user) for type safety and clarity.
        This method is for accessing other arbitrary data stored in the context dictionary
        via set_context().
        """
        return self._context.get(key, default)


    @property
    def context_data(self) -> Dict[str, Any]:
        """Provides public access to a combined view of context data."""
        logger.warning("Accessing raw context_data dictionary. Prefer using dedicated properties (e.g., request.user) or get_context().")
        return self._context

    @property
    def path_params(self) -> Dict[str, Any]:
        """Property to access path parameters extracted by the router."""
        params = self._context.get('path_params', {})
        return params if isinstance(params, dict) else {}

    @path_params.setter
    def path_params(self, params: Dict[str, Any]):
        """Setter for path parameters. Used by the router/AppController."""
        if not isinstance(params, dict):
             logger.warning(f"Attempted to set non-dictionary path_params on Request (method: {self.method}) for path: {self.path} type: {type(params)}")
             self._context['path_params'] = {}
        else:
             self._context['path_params'] = params

    @property
    def user(self) -> Optional[Any]:
        """Provides access to the authenticated user from request context."""
        return self.get_context('user')

    @user.setter
    def user(self, user: Optional[Any]):
        """Setter for the authenticated user, stored in _user internal attribute."""
        self._user = user
        self._context['user'] = user
        logger.debug(f"User set on request for {self.method} {self.path}: {user}")


    @property
    def session(self) -> Optional[AppSession]:
        """Provides access to the Session instance from request context."""
        return self.get_context('session')

    @session.setter
    def session(self, session_instance: Optional[AppSession]):
        """Setter for the Session instance, stored in _session internal attribute."""
        self._session = session_instance
        self._context['session'] = session_instance
        logger.debug(f"Session set on request for {self.method} {self.path}: {session_instance}")


    @property
    def db_session(self) -> Optional[SQLASession]:
        """Property to access the database session."""
        return self._db_session

    @db_session.setter
    def db_session(self, session: Optional[SQLASession]):
        """Setter for the database session. Used by SQLAlchemySessionMiddleware and set_context."""
        self._db_session = session
        self._context['db_session'] = session

        logger.debug(f"DB session set on Request (method: {self.method}, path: {self.path}): {session}")




    @property
    def config(self) -> Optional[Config]:
        """Provides access to the Config instance from request context."""
        return self.get_context('config')

    @config.setter
    def config(self, config_instance: Optional[Config]):
        """Setter for the Config instance, stored in _config internal attribute."""
        self._config = config_instance
        self._context['config'] = config_instance
        logger.debug(f"Config set on request for {self.method} {self.path}.")


    @property
    def template_renderer(self) -> Optional[TemplateRenderer]:
        """Provides access to the TemplateRenderer instance from request context."""
        return self.get_context('template_renderer')

    @template_renderer.setter
    def template_renderer(self, renderer: Optional[TemplateRenderer]):
        """Setter for the TemplateRenderer instance."""
        self._template_renderer = renderer
        self._context['template_renderer'] = renderer


    @property
    def router(self) -> Optional[Any]:
        """Provides access to the Router instance from request context."""
        return self.get_context('router')

    @router.setter
    def router(self, router_instance: Optional[Any]):
        """Setter for the Router instance."""
        self._router = router_instance
        self._context['router'] = router_instance


    @property
    def error_handler(self) -> Optional[ErrorHandler]:
        """Provides access to the ErrorHandler instance from request context."""
        return self.get_context('error_handler')

    @error_handler.setter
    def error_handler(self, handler: Optional[ErrorHandler]):
        """Setter for the ErrorHandler instance."""
        self._error_handler = handler
        self._context['error_handler'] = handler


    @property
    def dispatcher(self) -> Optional[SignalDispatcher]:
        """Provides access to the SignalDispatcher instance from request context."""
        return self.get_context('dispatcher')

    @dispatcher.setter
    def dispatcher(self, dispatcher_instance: Optional[SignalDispatcher]):
        """Setter for the SignalDispatcher instance."""
        self._dispatcher = dispatcher_instance
        self._context['dispatcher'] = dispatcher_instance


    @property
    def admin_registry(self) -> Optional[Any]:
        """Provides access to the AdminRegistry instance from request context."""
        return self.get_context('admin_registry')

    @admin_registry.setter
    def admin_registry(self, registry: Optional[Any]):
        """Setter for the AdminRegistry instance."""
        self._admin_registry = registry
        self._context['admin_registry'] = registry


    @property
    def environ(self) -> Dict[str, Any]:
        """Provides access to the raw WSGI environment dictionary."""
        return self._environ

    @property
    def admin_user_manager(self) -> Optional[Any]:
        """Provides access to the AdminUserManager instance from request context."""
        return self.get_context('admin_user_manager')

    @admin_user_manager.setter
    def admin_user_manager(self, manager: Optional[Any]):
        """Setter for the AdminUserManager instance."""
        self._admin_user_manager = manager
        self._context['admin_user_manager'] = manager


    @property
    def session_manager(self) -> Optional[Any]:
        """Provides access to the SessionManager instance from request context."""
        return self.get_context('session_manager')

    @session_manager.setter
    def session_manager(self, manager: Optional[Any]):
        """Setter for the SessionManager instance."""
        self._session_manager = manager
        self._context['session_manager'] = manager

    @property
    def user_manager(self) -> Optional[Any]:
        """Provides access to the UserManager instance from request context."""
        return self.get_context('user_manager')

    @user_manager.setter
    def user_manager(self, manager: Optional[Any]):
        """Setter for the UserManager instance."""
        self._user_manager = manager
        self._context['user_manager'] = manager 


    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the Request."""
        return (f"<Request(method='{getattr(self, 'method', 'N/A')}', path='{getattr(self, 'path', 'N/A')}', "
                f"query_params={getattr(self, 'query_params', {})}, "
                f"parsed_body_type={type(getattr(self, 'parsed_body', None))}, "
                f"files_keys={list(getattr(self, 'files', {}).keys())}, "
                f"cookies_keys={list(getattr(self, 'cookies', {}).keys())}, "
                f"context_keys={list(self._context.keys())}, "
                f"user={'<set>' if self._user is not None else '<not set>'}, "
                f"session={'<set>' if self._session is not None else '<not set>'}, "
                f"db_session={'<set>' if self._db_session is not None else '<not set>'} "
                f")>")
    

class TypeConverter:
    """Base class for path variable type converters."""
    def to_python(self, value: str) -> Any:
        """Converts the string value from the URL to a Python type."""
        raise NotImplementedError

    def to_url(self, value: Any) -> str:
        """Converts a Python value to its URL representation."""
        raise NotImplementedError

    @property
    def openapi_type(self) -> Dict[str, Any]:
        """Returns the OpenAPI schema type for this converter."""
        return {"type": "string"}

class IntegerConverter(TypeConverter):
    def to_python(self, value: str) -> int:
        return int(value)

    def to_url(self, value: Any) -> str:
        return str(value)

    @property
    def openapi_type(self) -> Dict[str, Any]:
        return {"type": "integer", "format": "int64"}

class UUIDConverter(TypeConverter):
    def to_python(self, value: str) -> 'uuid.UUID':
        import uuid
        return uuid.UUID(value)

    def to_url(self, value: Any) -> str:
        return str(value)

    @property
    def openapi_type(self) -> Dict[str, Any]:
        return {"type": "string", "format": "uuid"}