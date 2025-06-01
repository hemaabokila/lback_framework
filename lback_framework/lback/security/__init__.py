"""
This file serves as the initialization point for the 'lback_framework/lback/security' package.
It is designed to expose the core components necessary for implementing various security
measures and protections within the Lback web framework. This package centralizes the
definition and management of security-related functionalities, including firewall rules,
HTTP security headers, rate limiting, and protection against SQL injection, ensuring
the application's robustness against common web vulnerabilities.

---

**Key Components Exposed by this Package:**

1.  **AdvancedFirewall (from .firewall):**
    A component that provides advanced firewall capabilities for the Lback application.
    This class is responsible for defining and enforcing security rules at the network
    or application level, controlling access to resources based on various criteria
    such as IP addresses, request patterns, or user roles. It helps in preventing
    unauthorized access and mitigating denial-of-service (DoS) attacks.

2.  **SecurityHeadersConfigurator (from .headers):**
    A utility or class for configuring and applying various HTTP security headers to
    outgoing responses. This component helps to protect the application against a range
    of client-side attacks (e.g., XSS, clickjacking) by instructing browsers on how
    to behave when interacting with the application's content. Examples of headers
    include Content-Security-Policy (CSP), X-Frame-Options, and X-Content-Type-Options.

3.  **RateLimiter (from .rate_limiter):**
    A component that implements rate limiting functionality. This class is used to
    control the number of requests a client can make to the server within a given
    timeframe. It helps in preventing abuse, brute-force attacks, and resource
    exhaustion by limiting the frequency of requests from a single source.

4.  **SQLInjectionProtection (from .sql_injection):**
    A component dedicated to providing protection against SQL injection vulnerabilities.
    This class implements mechanisms (e.g., input sanitization, parameterized queries,
    or pattern detection) to prevent malicious SQL code from being injected into
    database queries through user input, thereby safeguarding the integrity and
    confidentiality of the application's data.
"""