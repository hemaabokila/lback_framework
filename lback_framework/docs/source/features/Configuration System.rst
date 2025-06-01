Configuration System
====================

Lback Framework allows you to manage your project's settings with high flexibility.

Settings are loaded in the following order (later sources override earlier ones):

1. ``.env`` **file:** Environment variables from this file are loaded first.
2. ``config.json`` **file:** Settings from this JSON file are loaded.
3. ``settings.py`` **file:** Settings defined in this Python file are loaded (typically your main settings).

4. **Actual Environment Variables:** Environment variables defined in the operating system override all previous sources.

You can access settings anywhere in your application through the ``config`` object, typically made available via Dependency Injection.

Core Project Settings
-------------------------------------------------------

    .. code-block:: python

        # Defines the name of your project. This is used for identification and internal referencing.
        PROJECT_NAME = "myproject"
        # Specifies the Python module that contains your project's URL patterns.
        # This module defines how incoming requests are routed to specific views.
        ROOT_URLCONF = 'myproject.urls'
        # A boolean flag that enables or disables debugging features.
        # Set to `True` during development for detailed error messages and development tools.
        # **IMPORTANT**: Always set this to `False` in a production environment for security and performance.
        DEBUG = True
        # Designates the API version for your application's endpoints.
        # This helps in managing different versions of your API.
        API_VERSION = "v1"


Database Configuration
----------------------

    .. code-block:: python

        # The database engine to be used for your application.
        # Common options include "sqlite3", "postgresql", "mysql", etc.
        DB_ENGINE = "sqlite3"
        # The name of your database. For SQLite, this is the file name (e.g., "db.sqlite").
        # For other database engines, it's the name of the database instance.
        DB_NAME = "db.sqlite"


Email (SMTP) Configuration
--------------------------

    .. code-block:: python

        # The hostname or IP address of your SMTP (Simple Mail Transfer Protocol) server.
        SMTP_SERVER = "smtp.example.com"  # Example: "smtp.gmail.com" for Gmail
        # The port number for your SMTP server.
        # Common ports are 587 (for TLS/STARTTLS) or 465 (for SSL).
        SMTP_PORT = 587
        # The username for authenticating with your SMTP server.
        # This is typically your email address.
        # **SECURITY NOTE**: In production, consider using environment variables for sensitive credentials
        # instead of hardcoding them here.
        EMAIL_USERNAME = "your_app_email@example.com" # Example: "app.notifications@example.com"
        # The password or application-specific password for your email account.
        # **SECURITY NOTE**: Similar to `EMAIL_USERNAME`, use environment variables in production.
        EMAIL_PASSWORD = "your_email_app_password" # Example: "abcd efgh ijkl mnop" (for app passwords)
        # The email address that will appear as the sender of outgoing emails.
        SENDER_EMAIL = "no-reply@your-domain.com" # Example: "noreply@example.com"
        # A boolean flag to enable or disable Transport Layer Security (TLS) for secure email communication.
        USE_TLS = True
        # The display name for the sender of emails.
        SENDER_NAME = "Your Application" # Example: "MyProject Notifications"


Logging Configuration
---------------------

    .. code-block:: python

        # The minimum logging level that will be processed and displayed.
        # Available levels (in increasing order of severity): "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
        LOGGING_LEVEL = "WARNING" 


Path Definitions
----------------

    .. code-block:: python

        # The absolute path to the base directory of your project.
        # This is typically the directory containing this `settings.py` file.
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # A synonym for `BASE_DIR`, often used for clarity when referring to the project's root.
        PROJECT_ROOT = BASE_DIR 


Static Files Configuration
--------------------------

    .. code-block:: python

        # The URL prefix for accessing static files (CSS, JavaScript, images, etc.) in your web application.
        # For example, if `STATIC_URL` is `/static/`, then a file `style.css` in your static directory
        # will be accessible at `/static/style.css`.
        STATIC_URL = '/static/'
        # The absolute path to the directory where all static files will be collected for deployment.
        # It's a common practice to use a dedicated directory like 'staticfiles' for this.
        STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 
        # A list of absolute paths to directories where the framework should look for static files.
        # This allows you to organize static files within apps or in a central project-level directory.
        STATIC_DIRS = [
            os.path.join(BASE_DIR, 'static'), # Your project's general static files
            # os.path.join(BASE_DIR, 'your_app_name', 'static'), # Example: add app-specific static dirs
        ]


Media Files (User Uploads) Configuration
----------------------------------------

    .. code-block:: python

        # The relative path within your project where user-uploaded files (e.g., images, documents) will be stored.
        UPLOAD_FOLDER = 'media/uploads'
        # The URL prefix for accessing user-uploaded media files.
        UPLOAD_URL = '/media/uploads/'


Installed Applications (Apps)
-----------------------------

    .. code-block:: python

        # A list of strings, each representing the name of an application installed in your project.
        # The framework will load these applications, enabling their features, models, views, and other components.
        INSTALLED_APPS = [
            "admin",    # Example: A built-in or custom admin interface app.
            # "auth_app", # Example: An application for user authentication and authorization.
        ]



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


Security Settings
-----------------

    .. code-block:: python

        # A list of hostnames (e.g., domain names, IP addresses) that your application is allowed to serve.
        # Requests with a Host header not matching any entry in this list will be rejected.
        ALLOWED_HOSTS = [
            "127.0.0.1", # Local development IP address
            "localhost", # Standard localhost hostname
            # "your-production-domain.com", # Add your live domain(s) here
        ]

        # Firewall specific settings for `FirewallMiddleware`.
        FIREWALL_SETTINGS = {
            # A list of IP addresses that are explicitly allowed to access the application.
            "ALLOWED_IPS": ["127.0.0.1"], 
            # "DENIED_IPS": ["192.168.1.100"], # Example: IPs explicitly denied access
        }

        # HTTP Security Headers configuration for `SecurityHeadersMiddleware`.
        SECURITY_HEADERS = {
            # Content Security Policy (CSP): A crucial security header that helps prevent XSS attacks
            # by specifying which sources of content (scripts, styles, images, etc.) are allowed to be loaded.
            # 'self': Allows resources only from your application's domain.
            # 'unsafe-inline': Allows inline scripts (<script> tags) and styles (<style> tags or style attributes).
            #                 Use sparingly, as it reduces CSP's effectiveness against XSS. Prefer external files.
            "CONTENT_SECURITY_POLICY": "default-src 'self'; "
                                    "script-src 'self' 'unsafe-inline'; " 
                                    "style-src 'self' 'unsafe-inline'; "  
                                    "font-src 'self'; "
                                    "img-src 'self'; "
                                    "connect-src 'self'; "
                                    "media-src 'none'; "       # Prevents loading of audio/video from any source
                                    "object-src 'none'; "      # Prevents loading of Flash, Java applets
                                    "frame-ancestors 'none';", # Prevents your site from being embedded in iframes

            # X-Frame-Options: Protects against Clickjacking attacks by preventing your site from being embedded in iframes.
            "X_FRAME_OPTIONS": "SAMEORIGIN", # Allows embedding only from the same origin. Use 'DENY' to disallow all.

            # Strict-Transport-Security (HSTS): Forces browsers to connect to your site only over HTTPS for a specified duration.
            "STRICT_TRANSPORT_SECURITY": "max-age=63072000; includeSubDomains; preload", # 2 years, applies to subdomains, and can be preloaded.

            # Referrer-Policy: Controls how much referrer information is sent with requests.
            "REFERRER_POLICY": "no-referrer-when-downgrade", # Sends referrer for HTTPS->HTTPS, not for HTTPS->HTTP.

            # Permissions-Policy (formerly Feature-Policy): Allows or denies the use of browser features and APIs.
            "PERMISSIONS_POLICY": "geolocation=(self)", # Example: Allows geolocation API usage only from your own origin.
        }

        # Rate Limiting specific settings for `RateLimitingMiddleware`.
        RATE_LIMITING_SETTINGS = {
            # The maximum number of requests allowed from a single client within the `WINDOW_SECONDS` timeframe.
            "MAX_REQUESTS": 100, 
            # The time window in seconds during which `MAX_REQUESTS` applies.
            "WINDOW_SECONDS": 60, 
        }

        # The duration, in minutes, after which a user's session will expire due to inactivity.
        SESSION_TIMEOUT_MINUTES = 30