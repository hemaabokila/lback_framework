import time
import logging

from lback.core.base_middleware import BaseMiddleware

logger = logging.getLogger(__name__)

class TimerMiddleware(BaseMiddleware):
    """
    A middleware component that measures and logs the processing time for each HTTP request.

    This middleware injects a start timestamp into the request object during the
    request processing phase and then calculates the total duration when the
    response is being processed. The duration is logged and also added as an
    'X-Response-Time' header to the outgoing response.
    """
    def process_request(self, request):
        """
        Records the starting timestamp for the incoming request.

        This timestamp is stored as a private attribute `_start_time` on the
        `request` object, which will be used later during response processing
        to calculate the total request duration.

        :param request: The incoming request object.
        :type request: Any
        :returns: None, allowing the request to proceed to the next middleware or view.
        :rtype: None
        """
        request._start_time = time.time()

    def process_response(self, request, response):
        """
        Calculates the duration of the request and logs it, then adds it to the response headers.

        This method retrieves the `_start_time` from the request object, calculates
        the elapsed time, logs this duration, and adds an `X-Response-Time` header
        to the outgoing response before returning it.

        :param request: The original request object, expected to have a `_start_time` attribute.
        :type request: Any
        :param response: The outgoing response object.
        :type response: Any
        :returns: The modified response object with the 'X-Response-Time' header.
        :rtype: Any
        """
        start_time = getattr(request, '_start_time', time.time())
        duration = time.time() - start_time
        response.headers["X-Response-Time"] = f"{duration:.4f}s"
        logger.info(f"{request.method} {request.path} -> {response.status_code} took {duration:.4f} seconds")
        return response
    

