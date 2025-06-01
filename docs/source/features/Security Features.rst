Security Features
=================

In addition to authentication and authorization, the framework provides tools and components to contribute to securing your application:

- **CSRF Protection:** Protection against Cross-Site Request Forgery attacks via Middleware.
- **CORS Handling:** Managing Cross-Origin Resource Sharing policies via Middleware.
- **SQL Injection Protection:** Mechanisms (often integrated into the ORM and database interactions).
- **XSS Protection:** Tools to protect against Cross-Site Scripting attacks (perhaps via input sanitization or safe template rendering).
- **Rate Limiting:** Controlling the rate of incoming requests to protect against Denial of Service attacks.
- **Security Headers:** Adding security headers to responses to enhance browser security.
- **Firewall:** Potentially a basic application-level firewall system.


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