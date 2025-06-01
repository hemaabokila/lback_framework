import logging

from lback.core.base_middleware import BaseMiddleware


logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """
    A middleware component for standardized logging of incoming HTTP requests and
    outgoing HTTP responses within the web application.

    This middleware aims to provide a clear and concise log of basic request/response
    flow, which is essential for monitoring application activity, identifying patterns,
    and assisting in general troubleshooting. It also includes a mechanism to filter
    sensitive information like Authorization headers from the logs for security.
    """
    def process_request(self, request):
        """
        Logs details of the incoming HTTP request.

        This method captures the request method, path, and headers. Sensitive headers,
        such as 'Authorization', are filtered and obfuscated in the logs to prevent
        exposure of sensitive data. It returns None to allow the request to proceed
        through the middleware stack.

        :param request: The request object containing details about the incoming HTTP request.
                        Expected to have `method`, `path`, and `headers` attributes.
        :type request: Any
        :returns: None, allowing the request to proceed to the next middleware or view.
        :rtype: None
        """
        headers = self._filter_sensitive_headers(request.headers)
        logging.info(f"[{request.method}] {request.path} - Headers: {headers}")

    def process_response(self, request, response):
        """
        Logs details of the outgoing HTTP response.

        This method captures the request method, path, and the response's status code,
        providing a quick overview of the outcome of the request. It must return
        the response object to continue the response processing.

        :param request: The original request object associated with this response.
        :type request: Any
        :param response: The response object containing details about the outgoing HTTP response.
                         Expected to have a `status_code` attribute.
        :type response: Any
        :returns: The response object, potentially after being logged.
        :rtype: Any
        """
        logging.info(f"[{request.method}] {request.path} -> {response.status_code}")
        return response

    def _filter_sensitive_headers(self, headers):
        """
        Filters out sensitive HTTP header values to prevent them from being logged.

        Specifically, it replaces the value of the 'Authorization' header with a placeholder
        to ensure credentials are not exposed in plain text in log files.

        :param headers: A dictionary of HTTP request headers.
        :type headers: Dict[str, str]
        :returns: A new dictionary with sensitive header values replaced by placeholders.
        :rtype: Dict[str, str]
        """
        filtered_headers = {}
        for key, value in headers.items():
            if key.lower() == "authorization":
                filtered_headers[key] = "*****"
            else:
                filtered_headers[key] = value
        return filtered_headers
    

   