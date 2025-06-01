"""
This file serves as the initialization point for the 'lback_framework/lback/middlewares' package.
It is designed to expose the core components necessary for implementing various middleware
functionalities within the Lback web framework. This package centralizes the definition
and management of middleware that process requests and responses globally or for specific
routes, enhancing application behavior for concerns like authentication, security, logging,
and session management.

---

**Key Components Exposed by this Package:**

1.  **AuthMiddleware (from .auth_midlewares):**
    A middleware component responsible for handling authentication processes. This middleware
    intercepts incoming requests to verify user credentials or session tokens, ensuring that
    only authenticated users can access protected resources. It integrates with the framework's
    authentication system.

2.  **BodyParsingMiddleware (from .body_parsing_middleware):**
    A middleware component designed to parse the body of incoming HTTP requests. This is crucial
    for handling different content types (e.g., JSON, form data, multipart/form-data for file uploads)
    and making the parsed data easily accessible to view functions.

3.  **CORSMiddleware (from .cors):**
    A middleware component that implements Cross-Origin Resource Sharing (CORS) policies.
    This middleware adds appropriate HTTP headers to responses, allowing web browsers to
    permit cross-origin requests to the Lback application, which is essential for
    single-page applications (SPAs) or APIs consumed from different domains.

4.  **CSRFMiddleware (from .csrf):**
    A middleware component that provides Cross-Site Request Forgery (CSRF) protection.
    This middleware helps prevent malicious attacks where unauthorized commands are
    transmitted from a user that the web application trusts. It typically involves
    generating and validating CSRF tokens.

5.  **DebugMiddleware (from .debug):**
    A middleware component that provides debugging functionalities, typically active
    only in development environments. This might include displaying detailed error
    messages, logging request/response information, or providing tools for inspecting
    application state during development.

6.  **LoggingMiddleware (from .logger):**
    A middleware component responsible for logging incoming requests and outgoing responses.
    This middleware captures information such as request method, URL, status code, and
    response time, providing valuable data for monitoring and debugging the application.

7.  **MediaFilesMiddleware (from .media_files_middleware):**
    A middleware component for serving user-uploaded media files. This middleware handles
    requests for files stored outside the static files directory, typically in a designated
    media folder, ensuring they are served correctly by the application.

8.  **Security Middlewares (from .security_middleware):**
    A collection of middleware components focused on enhancing the application's security posture.

    * **SecurityHeadersConfigurator:** A utility or class for configuring various security-related
        HTTP headers (e.g., X-Content-Type-Options, X-Frame-Options, Content-Security-Policy).
    * **SecurityHeadersMiddleware:** Applies the configured security headers to all outgoing responses,
        mitigating common web vulnerabilities.
    * **SQLInjectionDetectionMiddleware:** A middleware specifically designed to detect and potentially
        prevent SQL injection attempts by analyzing incoming request data for malicious patterns.
    * **SQLInjectionProtection:** A utility or class that provides the core logic for SQL injection
        protection, often used by the detection middleware.

9.  **SessionMiddleware (from .session_middleware):**
    A middleware component that enables session management for the application. This middleware
    establishes and maintains user sessions across multiple requests, allowing the application
    to store and retrieve user-specific data (e.g., login status, shopping cart contents)
    between interactions.

10. **SQLAlchemySessionMiddleware (from .sqlalchemy_middleware):**
    A middleware component specifically for integrating SQLAlchemy sessions with the request lifecycle.
    This middleware typically manages the creation, usage, and closing of database sessions
    for each incoming request, ensuring proper database connection management.

11. **StaticFilesMiddleware (from .static_files_middleware):**
    A middleware component for serving static assets (e.g., CSS, JavaScript, images) directly
    from the application. This middleware intercepts requests for static files and serves them
    efficiently, typically in development environments, before a production web server takes over.

12. **TimerMiddleware (from .timer):**
    A middleware component designed to measure and log the time taken to process each request.
    This middleware can be useful for performance monitoring and identifying bottlenecks
    in the application's request-response cycle.
"""