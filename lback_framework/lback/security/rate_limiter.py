import time
import threading

class RateLimiter:
    """
    Implements a generic rate limiting mechanism to control the frequency of operations
    or requests based on a specified key.

    This class tracks the number of requests made within a defined time window
    and prevents further requests if a maximum limit is exceeded. It is thread-safe,
    making it suitable for use in multi-threaded environments like web servers.
    """


    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initializes the RateLimiter with the maximum allowed requests and the time window.

        :param max_requests: The maximum number of requests allowed within the `window_seconds`.
        :type max_requests: int
        :param window_seconds: The time window (in seconds) during which `max_requests` are allowed.
        :type window_seconds: int
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self.lock = threading.Lock()
        

    def is_allowed(self, key: str) -> bool:
        """
        Checks if a request identified by a unique key is allowed based on the rate limit.

        This method logs the current request's timestamp. If the number of requests
        for the given key within the defined `window_seconds` exceeds `max_requests`,
        the request is denied. Otherwise, it is allowed.

        :param key: A unique identifier for the request source (e.g., IP address, user ID, API key).
        :type key: str
        :returns: True if the request is allowed by the rate limit, False otherwise.
        :rtype: bool
        """
        now = time.time()
        with self.lock:
            reqs = self.requests.get(key, [])
            reqs = [t for t in reqs if t > now - self.window_seconds]
            if len(reqs) >= self.max_requests:
                self.requests[key] = reqs
                return False
            reqs.append(now)
            self.requests[key] = reqs
            return True