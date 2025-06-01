import logging
import json
from typing import Optional, Dict
from datetime import datetime
from http import HTTPStatus

from lback.core.types import Request
from lback.core.response import Response
from lback.core.base_middleware import BaseMiddleware
from lback.utils.session_manager import SessionManager
from lback.utils.app_session import AppSession
from sqlalchemy.orm import Session as DBSession

logger = logging.getLogger(__name__)

class SessionMiddleware(BaseMiddleware):
    """
    Middleware to load session data at the start of the request and save
    session data (if modified) at the end of the request, using a database.
    Attaches a Session object (AppSession wrapper) to the request context using 'session'.
    Handles session cookie reading and writing.
    Requires SQLAlchemyMiddleware to run before it to provide the DB session.
    """
    def __init__(self, session_manager: SessionManager):
        """
        Initializes with a SessionManager instance (a dependency).
        Args:
            session_manager: The SessionManager instance for session storage operations.
        """
        self.session_manager = session_manager
        self._session_cookie_name = 'session_id'
        logger.info("SessionMiddleware initialized.")
    def process_request(self, request: Request) -> Optional[Response]:
        logger.debug("SessionMiddleware: Processing request.")

        db_session: Optional[DBSession] = request.get_context('db_session')
        if not db_session:
            logger.error("SessionMiddleware: Database session not found on request context. Ensure SQLAlchemyMiddleware runs before SessionMiddleware.")
            return Response(body=b"Internal Server Error: Database session not available for session handling.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value)
        
        session_id = self._get_session_id_from_cookie(request, self._session_cookie_name)
        session_data_payload = None
        is_new_session = False
        expires_at = None
        full_session_data_from_db = None

        if session_id:
            logger.debug(f"SessionMiddleware: Found session ID cookie: {session_id}. Attempting to load session from DB.")
            full_session_data_from_db = self.session_manager.get_session_data(db_session, session_id)
            
            if full_session_data_from_db:
                logger.debug(f"SessionMiddleware: Session data found in DB for ID {session_id}.")
                raw_data_string = full_session_data_from_db.get('data', '{}')
                expires_at = full_session_data_from_db.get('expires_at')

                if not isinstance(raw_data_string, str):
                    logger.warning(f"SessionMiddleware: Data for session ID {session_id} is not a string. Type: {type(raw_data_string)}. Attempting to convert.")
                    try:
                        raw_data_string = raw_data_string.decode('utf-8')
                    except (AttributeError, UnicodeDecodeError):
                        logger.error(f"SessionMiddleware: Could not convert session data to string for ID {session_id}. Treating as empty.", exc_info=True)
                        raw_data_string = "{}"

                try:
                    session_data_payload = json.loads(raw_data_string)
                    logger.debug(f"SessionMiddleware: Successfully decoded session data JSON for ID {session_id}. Keys: {list(session_data_payload.keys())}")
                except json.JSONDecodeError:
                    logger.error(f"SessionMiddleware: Failed to decode JSON data for session ID {session_id}. Treating session data as empty.", exc_info=True)
                    session_data_payload = {}
                except Exception as e:
                    logger.error(f"SessionMiddleware: Unexpected error processing session data for ID {session_id}: {e}", exc_info=True)
                    session_data_payload = {}

                self.session_manager.renew_session(db_session, session_id)
                logger.debug(f"SessionMiddleware: Renewed session ID {session_id}.")
            else:
                logger.debug(f"SessionMiddleware: Session ID {session_id} from cookie not found or expired in manager. Treating as no valid session.")
                session_id = None
                expires_at = None

        if session_data_payload is None:
            session_data_payload = {} 
            is_new_session = True
            expires_at = None 
            logger.debug("SessionMiddleware: Prepared data for a potential new session.")
        
        request_session_wrapper = AppSession(
            session_id=session_id,
            initial_data=session_data_payload,
            session_manager=self.session_manager,
            db_session=db_session,
            is_new=is_new_session,
            expires_at=expires_at
        )

        if hasattr(request, 'add_context') and callable(request.add_context):
            request.add_context('session', request_session_wrapper)
            logger.debug("SessionMiddleware: Attached Session wrapper to request context using add_context.")
        elif hasattr(request, '_context') and isinstance(request._context, dict):
            request._context['session'] = request_session_wrapper
            logger.debug("SessionMiddleware: Attached Session wrapper to request context using _context dictionary.")
        else:
            logger.error("SessionMiddleware: Request object does not support adding context data. Cannot attach session.")
        
        logger.debug("SessionMiddleware: Finished processing request.")
        return None
    def process_response(self, request: Request, response: Response) -> Response:
        """
        Saves the session data if it was modified during the request and adds
        the session cookie to the response if it's a new session or deleted.
        """
        logger.debug(f"SessionMiddleware: Processing response (status: {response.status_code}).")
        db_session: Optional[DBSession] = request.get_context('db_session')
        if not db_session:
            logger.error("SessionMiddleware: Database session not found on request context during response processing. Cannot save/process session.")
            return response 
        request_session_wrapper: Optional[AppSession] = request.get_context('session')
        if request_session_wrapper is None:
            logger.debug("SessionMiddleware: Could not retrieve Session wrapper from request context. Cannot save/process session.")
            return response 
        if request_session_wrapper.deleted:
            logger.debug("SessionMiddleware: Session was deleted during the request. Attempting to delete cookie.")
            self._delete_session_cookie(response, self._session_cookie_name)
            logger.debug("SessionMiddleware: Added Set-Cookie header to delete session cookie.")
        elif request_session_wrapper.modified or request_session_wrapper.is_new:
            logger.debug("SessionMiddleware: Session was modified or is new. Attempting to save.")
            saved_session_id = request_session_wrapper.save()

            if saved_session_id:
                session_manager_from_wrapper = request_session_wrapper._session_manager
                if session_manager_from_wrapper and hasattr(session_manager_from_wrapper, 'session_timeout'):
                     cookie_expiry_datetime = datetime.utcnow() + session_manager_from_wrapper.session_timeout
                     self._set_session_cookie(response, self._session_cookie_name, saved_session_id, cookie_expiry_datetime)
                     logger.debug(f"SessionMiddleware: Added Set-Cookie header for session ID {saved_session_id} with expiry {cookie_expiry_datetime}.")
                else:
                    logger.error("SessionMiddleware: SessionManager or its timeout not available in wrapper. Cannot set Set-Cookie header.")
            else:
                logger.warning("SessionMiddleware: Session was not successfully saved. Cannot add/update Set-Cookie header.")
        logger.debug("SessionMiddleware: Finished processing response.")
        return response
    def _get_session_id_from_cookie(self, request: Request, cookie_name: str) -> Optional[str]:
        """Extracts a specific cookie value (session ID) from the request headers."""
        cookie_header = request.headers.get('COOKIE')
        if not cookie_header:
            logger.debug(f"SessionMiddleware: No '{cookie_name}' cookie header in request.")
            return None
        cookies: Dict[str, str] = {}
        try:
            cookie_list = [c.strip() for c in cookie_header.split(';')]
            for cookie_pair in cookie_list:
                if '=' in cookie_pair:
                    key, value = cookie_pair.split('=', 1)
                    cookies[key] = value
        except Exception as e:
            logger.error(f"SessionMiddleware: Error parsing 'COOKIE' header: {e}")
            return None
        session_id = cookies.get(cookie_name)
        if session_id:
            logger.debug(f"SessionMiddleware: Found '{cookie_name}' cookie with ID: {session_id}")
            return session_id
        else:
            logger.debug(f"SessionMiddleware: '{cookie_name}' cookie not found in header.")
            return None

    def _set_session_cookie(self, response: Response, cookie_name: str, cookie_value: str, expires: datetime):
        """Sets a Set-Cookie header on the response."""
        expires_gmt = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        set_cookie_header_value = (
            f"{cookie_name}={cookie_value}; "
            f"Expires={expires_gmt}; "
            "Path=/; "
            "HttpOnly" 
        )
        if hasattr(response, 'headers') and isinstance(response.headers, dict):
            response.headers['Set-Cookie'] = set_cookie_header_value
        elif hasattr(response, 'headers') and isinstance(response.headers, list):
            found = False
            for i, (key, val) in enumerate(response.headers):
                if key.lower() == 'set-cookie':
                    response.headers[i] = ('Set-Cookie', set_cookie_header_value)
                    found = True
                    break
            if not found:
                 response.headers.append(('Set-Cookie', set_cookie_header_value))
        else:
            logger.error("SessionMiddleware: Response object does not have a dict-like or list-like 'headers' attribute. Cannot add Set-Cookie header.")

    def _delete_session_cookie(self, response: Response, cookie_name: str):
        """Deletes a cookie by setting its expiration to the past."""
        delete_cookie_header_value = f"{cookie_name}=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/"
        if hasattr(response, 'headers') and isinstance(response.headers, dict):
            response.headers['Set-Cookie'] = delete_cookie_header_value
        elif hasattr(response, 'headers') and isinstance(response.headers, list):
            found = False
            for i, (key, val) in enumerate(response.headers):
                if key.lower() == 'set-cookie':
                    response.headers[i] = ('Set-Cookie', delete_cookie_header_value)
                    found = True
                    break
            if not found:
                 response.headers.append(('Set-Cookie', delete_cookie_header_value))
        else:
            logger.error("SessionMiddleware: Response object does not have a dict-like or list-like 'headers' attribute. Cannot add Set-Cookie header for deletion.")

