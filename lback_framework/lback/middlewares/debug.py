import logging

from lback.core.base_middleware import BaseMiddleware

logger = logging.getLogger(__name__)

class DebugMiddleware(BaseMiddleware):
    """
    A middleware component designed for logging detailed information about
    incoming requests and outgoing responses within the web framework.

    This middleware is primarily used during development and debugging phases
    to gain insights into the data flow, headers, and body content of HTTP communications.
    It can be enabled or disabled and configured to log either requests, responses, or both.
    """
    def __init__(self, enabled=True, log_request=True, log_response=True, max_body_length=500):
        """
        Initializes the DebugMiddleware with logging preferences.

        :param enabled: A boolean indicating whether the middleware is active.
                        If False, no logging will occur. Defaults to True.
        :type enabled: bool
        :param log_request: A boolean indicating whether to log incoming request details. Defaults to True.
        :type log_request: bool
        :param log_response: A boolean indicating whether to log outgoing response details. Defaults to True.
        :type log_response: bool
        :param max_body_length: The maximum length (in characters/bytes) for logging request and response bodies.
                                Bodies exceeding this length will be truncated. Defaults to 500.
        :type max_body_length: int
        """
        self.enabled = enabled
        self.log_request = log_request
        self.log_response = log_response
        self.max_body_length = max_body_length
        logger.info(f"DebugMiddleware initialized (Enabled: {enabled}, Log Request: {log_request}, Log Response: {log_response}).")

    def process_request(self, request):
        """
        Logs details of the incoming HTTP request if the middleware is enabled and configured for request logging.

        This includes the request path, method, headers, and body (truncated if it exceeds `max_body_length`).
        As a `BaseMiddleware` method, it should return None to indicate that the request processing
        should continue to the next middleware or the view.

        :param request: The request object containing details about the incoming HTTP request.
                        Expected to have `path`, `method`, `headers`, and `body` attributes.
        :type request: Any
        :returns: None, allowing the request to proceed through the middleware stack.
        :rtype: None
        """
        if self.enabled and self.log_request:
            logger.debug(f"Request Path: {request.path}, Method: {request.method}")
            headers = request.headers if hasattr(request, 'headers') and request.headers else "No Headers"
            logger.debug(f"Headers: {headers}")
            if hasattr(request, 'body') and request.body:
                 body = self._truncate_body(request.body)
                 logger.debug(f"Body: {body}")
            else:
                 logger.debug("No Body")
        return None 

    def process_response(self, request, response):
        """
        Logs details of the outgoing HTTP response if the middleware is enabled and configured for response logging.

        This includes the response status code, and body (truncated if it exceeds `max_body_length`).
        As a `BaseMiddleware` method, it must return the `response` object, potentially modified,
        to be passed to the next middleware or back to the client.

        :param request: The original request object associated with this response.
        :type request: Any
        :param response: The response object containing details about the outgoing HTTP response.
                         Expected to have `status_code` and `body` attributes.
        :type response: Any
        :returns: The response object, potentially after being logged.
        :rtype: Any
        """
        if self.enabled and self.log_response:
            logger.debug(f"Processing response in DebugMiddleware for {request.method} {request.path}")
            if hasattr(response, 'status_code'): 
                 logger.debug(f"Response Status Code: {response.status_code}")
            else:
                 logger.warning("Response object has no 'status_code' attribute in DebugMiddleware.")
            if hasattr(response, 'body') and response.body:
                body = self._truncate_body(response.body) 
                logger.debug(f"Response Body: {body}")
            else:
                logger.debug("No Response Body or body is empty")
        return response

    def _truncate_body(self, body) -> bytes:
        """
        Helper method to truncate a string or bytes body if its length exceeds `max_body_length`.

        Appends "..." to the truncated body to indicate truncation.

        :param body: The body content (string or bytes) to potentially truncate.
        :type body: Any (str or bytes)
        :returns: The original body if shorter than `max_body_length`, or the truncated body.
        :rtype: Any (str or bytes)
        """
        if len(body) > self.max_body_length:
            if isinstance(body, bytes):
                return body[:self.max_body_length] + b"..."
            elif isinstance(body, str):
                return body[:self.max_body_length] + "..."
        return body