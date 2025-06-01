Authentication
==============

The framework provides a comprehensive and ready-to-use system for user management and **authentication**.

You can quickly integrate a full authentication flow into your application with minimal setup.

Quick Setup for Authentication
------------------------------

To enable and configure the built-in authentication system, follow these simple steps:

**1- Create Authentication Templates:**


The framework expects specific HTML templates for the authentication pages.

You just need to create these files in your ``templates`` directory (or wherever your framework is configured to look for templates):

* ``register.html``: For user registration.

    .. code-block:: html

        <form method="POST" action="/auth/register/">
            {% if csrf_token %}
            <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
            {% endif %}

            {{ form.as_p() | safe }}

            <button type="submit">Register</button>
        </form>

* ``auth_login.html``: For user login.

    .. code-block:: html

        <form method="POST" action="/auth/login/">
            {% if csrf_token %}
                <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
            {% endif %}
            {{ form.as_p() | safe }}
            <button type="submit">Login</button>
        </form>

* ``request_password_reset.html``: For requesting a password reset link.

    .. code-block:: html

        <form method="POST" action="/auth/request-reset-password/">
            {% if csrf_token %}
            <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
            {% endif %}

            {{ form.as_p() | safe }}

            <button type="submit">Request Reset Link</button>
        </form>

* ``reset_password_confirm.html``: For setting a new password after a reset request.

    .. code-block:: html

        <form method="POST" action="/auth/reset-password/">
            {% if csrf_token %}
            <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
            {% endif %}

            <input type="hidden" name="token" value="{{ reset_token }}">

            {{ form.as_p() | safe }}

            <button type="submit">Set New Password</button>
        </form>

These templates will automatically be rendered by the framework's internal authentication views, providing a consistent user experience.

**2- Add** ``auth_app`` **to** ``INSTALLED_APPS``:

Include the authentication application in your project's settings to enable its functionalities and ensure its views and models are loaded:

    .. code-block:: python
        
        # settings.py
        INSTALLED_APPS = [
            # ... other apps ...
            'auth_app', # Include the built-in authentication application
        ]

**3- Include Authentication URLs:**

Add the ``auth_app`` URLs to your project's main ``urlpatterns``.

This makes all the necessary authentication endpoints (both web-based and API) accessible:

    .. code-block:: python

        # myproject/urls.py
        from lback.core.urls_utils import include

        urlpatterns = [
            include('lback.auth_app.urls', prefix='/auth/'),
            include('lback.admin.urls', prefix='/admin/'),
            # ... other project URLs ...
        ]

**4- Configure Email Settings (for Password Resets & Email Verification):**

For features like password reset emails or email verification, you'll need to provide your SMTP server details in your ``settings.py``:

    .. code-block:: python

        # settings.py
        SMTP_SERVER = "smtp.gmail.com"  # Your SMTP server address
        SMTP_PORT = 587                 # Your SMTP server port (e.g., 587 for TLS, 465 for SSL)
        EMAIL_USERNAME = "your_email@example.com" # The email address for sending
        EMAIL_PASSWORD = "your_app_password" # The password for the sending email (use app-specific passwords for security)
        SENDER_EMAIL = "your_email@example.com" # The 'From' email address
        USE_TLS = True                  # Set to True for TLS/SSL encryption
        SENDER_NAME = "Your App Name"   # The sender name displayed in emails

**5- Configure the Default User Group ('basic_user'):**

Your framework's User Manager automatically assigns newly registered users to a default group named ``basic_user``. It is **crucial** to create and configure this group correctly in your admin panel to ensure new users have the necessary permissions to interact with your application.

**Purpose of** ``basic_user``:
    This group defines the base permissions for all standard, non-administrative users. Without this group, new users will not have any permissions assigned, severely limiting their access to your application's features.

**Mandatory Setup Steps:**

    1.  **Create the Group:** Log in to the **Admin Panel** (typically at ``/admin``).
        Navigate to **Authentication & Authorization** -> **User Groups**. Click on "Add Group" and name it ``basic_user``.

    2.  **Assign Permissions:** It is essential to assign the appropriate default permissions to the ``basic_user`` group. While specific permissions depend on your application's design, common permissions for a basic user include:
        * `app_name.view_content`: Allows users to view publicly accessible content (e.g., articles, products).
        * `app_name.edit_own_profile`: Grants permission to update their own user profile details.
        * `app_name.add_comment`: Allows users to post comments or submit forms.
        * `app_name.access_dashboard`: (If applicable) Grants access to a basic user dashboard.

        **Please refer to your application's specific requirements to determine the full list of permissions necessary for a**  ``basic_user``.Select these permissions from the "Available permissions" list and add them to the ``basic_user`` group.

    3.  **Save:** Click "Save" to create and configure the group.

**Important Considerations:**
    * **Automation:** Currently, this group needs to be created manually. For production deployments, consider scripting this step (e.g., as part of a post-deployment script or initial data migration) to ensure consistency and prevent errors.
    * **Security:** Always follow the principle of least privilege. Grant ``basic_user`` only the permissions absolutely necessary for core functionality.
    * **Scalability:** As your application evolves, you might introduce other user groups (e.g., 'premium_user', 'moderator'). Ensure their permissions are carefully defined relative to 'basic_user'.

This setup enables the framework to send transactional emails required for the authentication process.

What the System Provides Automatically
--------------------------------------

Once configured, the framework's authentication system automatically handles:

* **Session-based Authentication:** Manages user sessions using cookies.
* **JWT Authentication:** Supports JSON Web Tokens for API authentication.
* **Secure Password Hashing:** Stores passwords securely using industry-standard hashing.
* **Pre-built Views & Endpoints:** Provides all necessary URL routes and underlying logic for registration, login, logout, email verification, and password reset (both web-based and API endpoints).
* **User Managers:** Utilizes internal helper classes (``UserManager``, ``AdminUserManager``, ``SessionManager``) for efficient user and session management.

Authentication Endpoints Reference
----------------------------------

The authentication system exposes both web-based URLs for rendering HTML pages and API endpoints for programmatic access (e.g., from a single-page application or mobile app).

Web-based Authentication Endpoints
----------------------------------

These URLs are primarily used for rendering HTML forms and handling form submissions for user authentication in traditional web applications.

**Registration Page:**

* **URL:** /auth/register/
* **Method:** GET
* **Description:** Displays the user registration form.
* **Named URL:** web_register_page

**Handle Registration Submission:**

* **URL:** /auth/register/
* **Method:** POST
* **Description:** Processes the submitted registration form data.
* **Named URL:** web_handle_register_submit

**Login Page:**

* **URL:** /auth/login/
* **Method:** GET
* **Description:** Displays the user login form.
* **Named URL:** web_login_page

**Handle Login Submission:**

* **URL:** /auth/login/
* **Method:** POST
* **Description:** Processes the submitted login credentials.
* **Named URL:** web_handle_login_submit

**Request Password Reset Page:**

* **URL:** /auth/request-reset-password/
* **Method:** GET
* **Description:** Displays the form to request a password reset email.
* **Named URL:** web_request_reset_password_page

**Handle Request Password Reset Submission:**

* **URL:** /auth/request-reset-password/
* **Method:** POST
* **Description:** Processes the request for a password reset email.
* **Named URL:** web_handle_request_password_reset_submit

**Reset Password Confirmation Page:**

* **URL:** /auth/reset-password-confirm/
* **Method:** GET
* **Description:** Displays the form to set a new password, typically accessed via a link from a password reset email. Requires a token query parameter.
* **Named URL:** web_reset_password_confirm_page

**Handle Reset Password Confirmation Submission:**

* **URL:** /auth/reset-password/
* **Method:** POST
* **Description:** Processes the new password submission for a reset request.
* **Named URL:** web_handle_reset_password_confirm_submit

**Verify Email:**

* **URL:** /auth/verify-email/
* **Method:** GET
* **Description:** Verifies a user's email address, typically accessed via a link sent to the user's email. Requires a token query parameter.
* **Named URL:** web_verify_email

**Logout User:**

* **URL:** /auth/logout/
* **Method:** POST, GET
* **Description:** Logs out the currently authenticated user.
* **Named URL:** web_logout_user (for POST), web_logout_user_get (for GET)

API Authentication Endpoints
----------------------------

These URLs are designed for use by API clients (e.g., JavaScript frontends, mobile applications) to programmatically interact with the authentication system. They typically return JSON responses.

**Register User:**

* **URL:** /api/auth/register/
* **Method:** POST
* **Description:** Registers a new user. Expects JSON data (e.g., username, email, password, password_confirm).
* **Named URL:** api_register_user
* **Authentication Required:** No

**Login User:**

* **URL:** /api/auth/login/
* **Method:** POST
* **Description:** Authenticates a user and issues authentication tokens (e.g., JWT). Expects JSON data (e.g., identifier (username or email), password).
* **Named URL:** api_login_user
* **Authentication Required:** No

**Verify Email:**

* **URL:** /api/auth/verify-email/
* **Method:** GET
* **Description:** Verifies a user's email address using a provided token. Returns a JSON response indicating success or failure.
* **Named URL:** api_verify_email
* **Authentication Required:** No

**Request Password Reset:**

* **URL:** /api/auth/request-reset-password/
* **Method:** POST
* **Description:** Requests a password reset link to be sent to the user's email. Expects JSON data (e.g., email).
* **Named URL:** api_request_reset_password
* **Authentication Required:** No

**Reset Password:**

* **URL:** /api/auth/reset-password/
* **Method:** POST
* **Description:** Sets a new password for a user using a reset token. Expects JSON data (e.g., token, new_password, confirm_new_password).
* **Named URL:** api_reset_password
* **Authentication Required:** No