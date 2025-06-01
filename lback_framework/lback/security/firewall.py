import ipaddress
import logging
import re
import time
import threading
from typing import List, Optional

logger = logging.getLogger(__name__)

class AdvancedFirewall:
    """
    A robust and customizable firewall system for filtering incoming requests
    based on IP addresses, networks, user agents, URL patterns, and basic DDoS detection.

    This class helps protect your application from malicious traffic by providing
    various blocking mechanisms and a rate-limiting system to mitigate distributed
    denial-of-service (DDoS) attacks.

    It is designed to be integrated into the request/response cycle of a web framework,
    typically as a middleware or a pre-processing step.
    """

    def __init__(
        self,
        allowed_ips: Optional[List[str]] = None,
        blocked_ips: Optional[List[str]] = None,
        blocked_networks: Optional[List[str]] = None,
        blocked_user_agents: Optional[List[str]] = None,
        blocked_url_patterns: Optional[List[str]] = None,
        ddos_max_requests: int = 100,
        ddos_window_seconds: int = 10,
        temp_block_seconds: int = 300
    ):
        """
        Initializes the AdvancedFirewall with specified rules and DDoS detection parameters.

        :param allowed_ips: A list of IP addresses explicitly allowed to access the application.
                            If provided, only IPs in this list are allowed.
        :type allowed_ips: Optional[List[str]]
        :param blocked_ips: A list of specific IP addresses to block.
        :type blocked_ips: Optional[List[str]]
        :param blocked_networks: A list of IP network strings (e.g., "192.168.1.0/24") to block.
        :type blocked_networks: Optional[List[str]]
        :param blocked_user_agents: A list of User-Agent strings to block.
        :type blocked_user_agents: Optional[List[str]]
        :param blocked_url_patterns: A list of regular expression strings for URLs to block.
                                     Case-insensitive matching is applied.
        :type blocked_url_patterns: Optional[List[str]]
        :param ddos_max_requests: The maximum number of requests allowed from a single IP
                                  within the `ddos_window_seconds` before temporary blocking.
        :type ddos_max_requests: int
        :param ddos_window_seconds: The time window (in seconds) for DDoS detection.
        :type ddos_window_seconds: int
        :param temp_block_seconds: The duration (in seconds) for which an IP is
                                   temporarily blocked due to suspected DDoS activity.
        :type temp_block_seconds: int
        """
        self.allowed_ips = set(allowed_ips) if allowed_ips else set()
        self.blocked_ips = set(blocked_ips) if blocked_ips else set()
        self.blocked_networks = [ipaddress.ip_network(net) for net in (blocked_networks or [])]
        self.blocked_user_agents = set(blocked_user_agents) if blocked_user_agents else set()
        self.blocked_url_patterns = [re.compile(pat, re.IGNORECASE) for pat in (blocked_url_patterns or [])]
        self.ddos_max_requests = ddos_max_requests
        self.ddos_window_seconds = ddos_window_seconds
        self.temp_block_seconds = temp_block_seconds
        self._request_log = {}
        self._temp_blocked = {}
        self._lock = threading.Lock()

    def _is_temp_blocked(self, ip: str) -> bool:
        """
        Checks if an IP address is currently under a temporary block.
        Removes expired temporary blocks.

        :param ip: The IP address to check.
        :type ip: str
        :returns: True if the IP is currently temporarily blocked, False otherwise.
        :rtype: bool
        """
        with self._lock:
            unblock_time = self._temp_blocked.get(ip)
            if unblock_time and time.time() < unblock_time:
                return True
            elif unblock_time:
                del self._temp_blocked[ip]
        return False

    def _log_request(self, ip: str) -> bool:
        """
        Logs a request from a given IP and checks for DDoS activity.
        If the request rate exceeds `ddos_max_requests` within `ddos_window_seconds`,
        the IP is temporarily blocked.

        :param ip: The IP address of the incoming request.
        :type ip: str
        :returns: True if the request is within the allowed rate limit, False if it leads to a temporary block.
        :rtype: bool
        """
        now = time.time()
        with self._lock:
            reqs = self._request_log.get(ip, [])
            reqs = [t for t in reqs if t > now - self.ddos_window_seconds]
            reqs.append(now)
            self._request_log[ip] = reqs
            
            if len(reqs) > self.ddos_max_requests:
                self._temp_blocked[ip] = now + self.temp_block_seconds
                logger.warning(f"IP {ip} temporarily blocked due to suspected DDoS.")
                return False
        return True

    def is_allowed(self, ip: str, user_agent: str = "", url: str = "") -> bool:
        """
        Determines if an incoming request is allowed based on configured firewall rules
        (IPs, networks, user agents, URL patterns) and DDoS detection.

        The checks are performed in a specific order:
        1. Temporary blocks (DDoS mitigation).
        2. Explicitly blocked IPs.
        3. IPs within blocked networks.
        4. Explicitly allowed IPs (if `allowed_ips` list is not empty).
        5. Blocked User-Agents.
        6. Blocked URL patterns.
        7. DDoS rate limiting check.

        :param ip: The IP address of the request origin.
        :type ip: str
        :param user_agent: The User-Agent string from the request header. Defaults to empty string.
        :type user_agent: str
        :param url: The full URL of the request. Defaults to empty string.
        :type url: str
        :returns: True if the request is allowed, False otherwise.
        :rtype: bool
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            logger.warning(f"Invalid IP address format received: {ip}")
            return False

        if self._is_temp_blocked(ip):
            logger.info(f"Access denied: IP {ip} is temporarily blocked.")
            return False

        if ip in self.blocked_ips:
            logger.info(f"Access denied: Explicitly blocked IP {ip}.")
            return False

        for net in self.blocked_networks:
            if ip_obj in net:
                logger.info(f"Access denied: IP {ip} is within blocked network {net}.")
                return False

        if self.allowed_ips and ip not in self.allowed_ips:
            logger.info(f"Access denied: IP {ip} not in allowed list.")
            return False

        if user_agent and user_agent in self.blocked_user_agents:
            logger.info(f"Access denied: Blocked User-Agent '{user_agent}'.")
            return False

        for pattern in self.blocked_url_patterns:
            if pattern.search(url):
                logger.info(f"Access denied: URL '{url}' matched blocked pattern '{pattern.pattern}'.")
                return False

        if not self._log_request(ip):
            logger.info(f"Access denied: IP {ip} triggered DDoS rate limit.")
            return False

        return True

    def block_ip(self, ip: str, temp: bool = False):
        """
        Adds an IP address to the blocked list.

        :param ip: The IP address to block.
        :type ip: str
        :param temp: If True, the IP is temporarily blocked for `temp_block_seconds`.
                     Otherwise, it's added to the permanent blocked IPs list.
        :type temp: bool
        """
        if temp:
            with self._lock:
                self._temp_blocked[ip] = time.time() + self.temp_block_seconds
            logger.info(f"IP {ip} temporarily blocked for {self.temp_block_seconds} seconds via manual call.")
        else:
            self.blocked_ips.add(ip)
            logger.info(f"IP {ip} added to permanent blocked list.")

    def unblock_ip(self, ip: str):
        """
        Removes an IP address from both the permanent and temporary blocked lists.

        :param ip: The IP address to unblock.
        :type ip: str
        """
        if ip in self.blocked_ips:
            self.blocked_ips.discard(ip)
            logger.info(f"IP {ip} removed from permanent blocked list.")
        with self._lock:
            if ip in self._temp_blocked:
                self._temp_blocked.pop(ip, None)
                logger.info(f"IP {ip} removed from temporary blocked list.")

    def add_blocked_user_agent(self, user_agent: str):
        """
        Adds a User-Agent string to the list of blocked user agents.

        :param user_agent: The User-Agent string to block.
        :type user_agent: str
        """
        self.blocked_user_agents.add(user_agent)
        logger.info(f"User-Agent '{user_agent}' added to blocked list.")

    def add_blocked_url_pattern(self, pattern: str):
        """
        Adds a URL regex pattern to the list of blocked URL patterns.

        :param pattern: The regular expression string for URLs to block.
        :type pattern: str
        """
        self.blocked_url_patterns.append(re.compile(pattern, re.IGNORECASE))
        logger.info(f"URL pattern '{pattern}' added to blocked list.")