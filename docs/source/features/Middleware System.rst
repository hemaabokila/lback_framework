Middleware System
=================
Middlewares are components that process requests and responses in a chain before and after they reach the View.

They can be used for common tasks like authentication, logging requests, adding security headers, managing database sessions, and more.

The list of Middlewares is defined in your project's settings (typically in ``settings.py``).

Middleware Configuration
------------------------

    .. code-block:: python

        # A list of middleware classes that process incoming requests and outgoing responses.
        # Middlewares are executed in the order they appear for requests (from top to bottom),
        # and in reverse order for responses (from bottom to top).
        MIDDLEWARES = [
            # Manages database sessions (e.g., SQLAlchemy sessions) for each request, ensuring proper connection handling.
            "lback.middlewares.sqlalchemy_middleware.SQLAlchemySessionMiddleware",
            # Handles serving user-uploaded media files, routing requests to the correct upload directory.
            {
                "class": "lback.middlewares.media_files_middleware.MediaFilesMiddleware",
                "params": {} # Middleware-specific parameters (e.g., allowed file types, max size).
            },
            # Manages the serving of static assets (CSS, JavaScript, images) from your project's static directories.
            "lback.middlewares.static_files_middleware.StaticFilesMiddleware",
            # Provides session management capabilities, allowing user-specific data to persist across multiple requests.
            {
                "class": "lback.middlewares.session_middleware.SessionMiddleware",
                "params": {}
            },
            # Implements network access control, allowing or denying requests based on IP addresses.
            {
                "class": "lback.middlewares.firewall_middleware.FirewallMiddleware",
                "params": {}
            },
            # Protects against brute-force attacks and resource exhaustion by limiting the number of requests
            # from a single client within a specified time window.
            {
                "class": "lback.middlewares.rateLimiting_middleware.RateLimitingMiddleware",
                "params": {}
            },
            # Scans incoming request data for patterns indicative of SQL injection attempts and blocks malicious queries.
            {
                "class": "lback.middlewares.sql_injection_detection_middleware.SQLInjectionDetectionMiddleware",
                "params": {}
            },
            # Parses the body of incoming HTTP requests, making form data, JSON, and other content types accessible.
            "lback.middlewares.body_parsing_middleware.BodyParsingMiddleware",
            # Handles user authentication and authorization, verifying credentials and attaching user information to the request.
            "lback.middlewares.auth_midlewares.AuthMiddleware",
            # Implements Cross-Site Request Forgery (CSRF) protection to prevent unauthorized commands from being executed.
            "lback.middlewares.csrf.CSRFMiddleware",
            # Configures Cross-Origin Resource Sharing (CORS) policies, controlling which external domains can access your API.
            {
                "class": "lback.middlewares.cors.CORSMiddleware",
                "params": {
                    "allow_origins": ["*"], # A list of origins (domains) allowed to make cross-origin requests. Use "*" for all (less secure for production).
                    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], # HTTP methods allowed for cross-origin requests.
                    "allow_headers": ["*"] # HTTP headers allowed in cross-origin requests.
                }
            },
            # Logs details about incoming requests and outgoing responses for debugging and monitoring.
            "lback.middlewares.logger.LoggingMiddleware",
            # Measures and logs the processing time for each request, useful for performance monitoring.
            "lback.middlewares.timer.TimerMiddleware",
            # Provides extensive debugging capabilities, including detailed request/response logging.
            # Only enable in development environments.
            {
                "class": "lback.middlewares.debug.DebugMiddleware",
                "params": {
                    "enabled": True, # Set to `True` to activate this debug middleware.
                    "log_request": True, # Log full details of the incoming HTTP request.
                    "log_response": True # Log full details of the outgoing HTTP response.
                }
            },
            # Adds various HTTP security headers to all responses to enhance browser-side security.
            {
                "class": "lback.middlewares.security_headers_middleware.SecurityHeadersMiddleware",
                "params": {}
            },
        ]

The framework provides a set of built-in Middlewares (as seen in the logs):

- `SQLAlchemySessionMiddleware`: Manages database sessions per request.
- `MediaFilesMiddleware`: Serves media files.
- `StaticFilesMiddleware`: Serves static files.
- `SessionMiddleware`: Manages user sessions.
- `FirewallMiddleware`: Acts as an internal firewall.
- `RateLimitingMiddleware`: Limits request rates.
- `SQLInjectionDetectionMiddleware`: Detects and prevents SQL injection.
- `BodyParsingMiddleware`: Parses and prepares request body data.
- `AuthMiddleware`: Handles authentication (Session and JWT).
- `CSRFMiddleware`: Provides protection against Cross-Site Request Forgery attacks.
- `CORSMiddleware`: Manages Cross-Origin Resource Sharing policies.
- `LoggingMiddleware`: Logs request and response details.
- `TimerMiddleware`: Measures and logs request response time.
- `DebugMiddleware`: Displays debugging information and request/response details during development.
- `SecurityHeadersMiddleware`: Adds HTTP security headers.

The framework also supports Dependency Injection in Middlewares, making it easy to access other components (like the Config, Loggers, Managers) from within a Middleware.