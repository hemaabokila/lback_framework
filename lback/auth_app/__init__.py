"""
This file serves as the initialization point for the 'lback_framework/lback/auth_app' package.
It is designed to expose the core components necessary for handling user authentication
and authorization processes specifically for web-based applications within the Lback framework.
This package centralizes the definition and management of user-facing authentication flows,
including rendering login/registration pages and processing form submissions.

---

**Key Components Exposed by this Package:**

1.  **Web Authentication Views (from .web_auth_views):**
    A collection of views specifically designed to render HTML pages and handle form submissions
    for user authentication processes in a web application context. These views manage the
    user interface aspects of authentication.

    * **show_login_page:** Renders the HTML page containing the user login form.
    * **show_register_page:** Renders the HTML page containing the user registration form.
    * **show_reset_password_confirm_page:** Renders the HTML page for users to confirm and set
        a new password after a reset request.
    * **show_request_password_reset_page:** Renders the HTML page where users can request a
        password reset link (e.g., by entering their email).
    * **handle_login_submit:** Processes the form submission from the login page, authenticates
        the user, and manages session creation.
    * **handle_register_submit:** Processes the form submission from the registration page,
        validates user data, and creates a new user account.
    * **handle_reset_password_confirm_submit:** Processes the form submission for setting a new
        password after a reset request, validating the token and new password.
    * **handle_request_password_reset_submit:** Processes the form submission for requesting a
        password reset, typically sending an email with a reset link.
    * **verify_email_web_view:** A web view to handle email verification links, confirming a user's
        email address.
    * **logout_user_view:** Handles user logout requests, terminating the user's session.

2.  **urlpatterns (from .urls):**
    A list or collection of URL patterns specifically for the authentication application. These patterns
    map incoming HTTP requests to the appropriate web authentication views, defining the routing
    for all user-facing authentication functionalities (e.g., /login/, /register/, /password-reset/).

3.  **API Authentication Views (from .auth_views):**
    A set of views that likely provide API endpoints for authentication functionalities,
    which might be consumed by client-side applications (e.g., single-page applications)
    or mobile apps, rather than rendering full HTML pages.

    * **register_user_view:** An API endpoint for user registration.
    * **login_user_view:** An API endpoint for user login.
    * **request_password_reset_view:** An API endpoint for initiating a password reset process.
    * **reset_password_view:** An API endpoint for completing the password reset process.
    * **verify_email_view:** An API endpoint for email verification.
"""