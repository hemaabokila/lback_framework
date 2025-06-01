Modules and Classes Reference
=============================

The **lback** framework is a modular and comprehensive web framework designed for building scalable and maintainable web applications. This document provides a detailed reference to all its key modules and the classes they encapsulate, highlighting their functionalities and contributions to the framework's overall architecture.

---

Core Modules
------------

The core modules form the fundamental backbone of the lback framework, handling essential operations, configurations, and the overall lifecycle of the application.

- **lback.core**: This module is the heart of the framework, providing core functionalities for application management.
- **AppController**: Manages the application's lifecycle and integrates various components.
- **BaseMiddleware**: The base class for all middlewares, defining the interface for middleware components.
- **Cache**: Provides caching mechanisms for performance optimization.
- **CacheItem**: Represents an item stored within the cache.
- **Config**: The central object for accessing application configurations and settings.
- **SettingsFileHandler**: Manages reading and writing application settings from files.
- **load_config, load_settings_module, update_config, start_settings_watcher, sync_settings_to_config, get_project_root**: Utility functions for managing application configuration.
- **dispatcher (from lback.core.dispatcher_instance)**: The central signal dispatcher instance for inter-component communication.
- **ErrorHandler**: Handles exceptions and generates appropriate error responses.
- **FrameworkException, Forbidden, HTTPException, BadRequest, NotFound, RouteNotFound, MethodNotAllowed, Unauthorized, ConfigurationError, ValidationError, ServerError**: A hierarchy of custom exceptions for various error conditions.
- **setup_logging**: Configures the logging system for the application.
- **load_middlewares_from_config, create_middleware, import_class**: Functions for loading and managing middleware instances.
- **MiddlewareManager**: Manages the execution flow of registered middlewares.
- **Middleware**: Represents a single middleware instance.
- **RedirectResponse, Response, HTMLResponse, JSONResponse**: Classes for constructing different types of HTTP responses.
- **Route**: Represents a single defined route in the application's routing table.
- **Router**: Manages all defined routes and dispatches incoming requests to the correct handler.
- **Server**: The main class responsible for starting and managing the web server.
- **initialize_core_components, wsgi_application**: Functions for initialising framework components and the WSGI application entry point.
- **SignalDispatcher**: Manages signals and slots for event-driven communication.
- **TemplateRenderer**: Handles rendering of HTML templates.
- **default_global_context, custom_uppercase, custom_url_tag**: Utilities for template rendering context and custom filters/tags.
- **Request**: Represents an incoming HTTP request.
- **HTTPMethod**: Enum for standard HTTP methods.
- **TypeConverter, UploadedFile, UUIDConverter, IntegerConverter**: Utilities for type conversion and handling uploaded files in routes.
- **Include (from lback.core.urls_utils)**: Utility for including URL patterns from other modules.
- **WebSocketServer**: Provides functionality for WebSocket communication.
- **create_wsgi_app**: Creates the WSGI application instance.

---

Authentication Modules
----------------------

These modules provide comprehensive tools for user authentication, authorization, and session management, covering various security protocols.

- **lback.auth**: Manages different authentication backends and security features.
- **SessionAuth**: Implements session-based user authentication.
- **PermissionRequired**: A decorator or class for enforcing permission-based access control.
- **PasswordHasher**: Handles secure hashing and verification of user passwords.
- **OAuth2Auth**: Provides integration for OAuth 2.0 authentication flows.
- **JWTAuth**: Implements JSON Web Token based authentication.
- **AdminAuth**: Specific authentication mechanisms for the admin panel users.

- **lback.auth_app**: Provides web-based views for user authentication and account management.
- **urlpatterns**: URL patterns for the authentication web views.
- **show_login_page, show_register_page, show_reset_password_confirm_page, show_request_password_reset_page**: Views for displaying authentication-related web pages.
- **handle_login_submit, handle_register_submit, handle_reset_password_confirm_submit, handle_request_password_reset_submit**: Views for handling form submissions related to authentication.
- **verify_email_web_view**: Web view for email verification.
- **logout_user_view**: View for logging out a user.
- **register_user_view, login_user_view, request_password_reset_view, reset_password_view, verify_email_view**: API-like views for authentication processes (could be used by web views or direct API calls).

---

API Layer
---------

The API layer offers robust tools for building RESTful APIs, including serialisation, generic views, and API documentation.

- **lback.api**: Core components for building API endpoints.
- **APIDocs (from lback.api.docs)**: Generates interactive API documentation.
- **GenericAPIView**: A base class for API views with common functionalities.
- **ListAPIView**: Generic view for listing multiple API resources.
- **CreateAPIView**: Generic view for creating new API resources.
- **RetrieveAPIView**: Generic view for retrieving a single API resource.
- **UpdateAPIView**: Generic view for updating an existing API resource.
- **DestroyAPIView**: Generic view for deleting an API resource.
- **ListCreateAPIView**: Combines listing and creation functionalities.
- **RetrieveUpdateDestroyAPIView**: Combines retrieve, update, and destroy functionalities.
- **ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin**: Mixins providing common API functionalities to views.
- **Field, BooleanField, BaseModelSerializer, IntegerField, StringField, RelatedField, DateTimeField**: Classes for defining and working with API serializers and their fields.
- **APIView**: The base class for defining custom API views.
- **BaseView**: A foundational base class for all views (API and web).

---

Admin Interface
---------------

lback includes a powerful built-in admin panel for managing application data and users.

- **lback.admin**: Provides the core functionality and views for the administrative interface.
- **admin**: The central Admin instance for registering models and managing admin settings.
- **AdminRegistry**: Manages the registration of models with the admin panel.
- **urlpatterns**: URL patterns specific to the admin interface.
- **admin_user_add_view, admin_user_list_view**: Views for managing admin users.
- **generic_add_view, generic_list_view, generic_delete_view, generic_change_view, generic_detail_view**: Generic views for performing CRUD (Create, Read, Update, Delete) operations on registered models.
- **admin_login_page, admin_dashboard_page, admin_login_post, admin_logout_post**: Views for admin authentication and dashboard.

---

Middleware
----------

The middleware system in lback allows for flexible and extensible request/response processing.

- **lback.middlewares**: A collection of pre-built and pluggable middleware components.
- **AuthMiddleware**: Handles authentication processing for requests.
- **BodyParsingMiddleware**: Parses request bodies (e.g., JSON, form data).
- **CORSMiddleware**: Manages Cross-Origin Resource Sharing headers.
- **CSRFMiddleware**: Provides protection against Cross-Site Request Forgery attacks.
- **DebugMiddleware**: Assists in debugging by providing insights into request processing.
- **LoggingMiddleware**: Logs incoming requests and outgoing responses.
- **MediaFilesMiddleware**: Serves media files (user-uploaded content).
- **SecurityHeadersConfigurator, SecurityHeadersMiddleware**: Configures and applies security-related HTTP headers.
- **SQLInjectionDetectionMiddleware, SQLInjectionProtection**: Detects and helps prevent SQL injection vulnerabilities.
- **SessionMiddleware**: Manages user sessions.
- **SQLAlchemySessionMiddleware**: Manages SQLAlchemy database sessions within requests.
- **StaticFilesMiddleware**: Serves static files (CSS, JS, images).
- **TimerMiddleware**: Measures and logs request processing times.

---

Forms
-----

lback provides a robust form system for handling user input, validation, and rendering.

- **lback.forms**: Core module for form definition and processing.
- **Form**: The base class for all forms.
- **FormMetaclass**: Metaclass for form creation.
- **ModelForm**: A special type of form automatically generated from a database model.
- **ValidationError (from lback.forms.validation)**: Exception raised for form validation errors.

- **lback.forms.fields_datetime**: Specific field types for date and time inputs.
- **DateTimeField**: Form field for date and time.
- **TimeField**: Form field for time.
- **DateField**: Form field for date.

- **lback.forms.fields_file**: Field type for file uploads.
- **FileField**: Form field for handling file uploads.

- **lback.forms.fields**: General purpose form field types.
- **BooleanField**: Form field for boolean (checkbox) input.
- **CharField**: Form field for text input.
- **ChoiceField**: Form field for selection from predefined choices.
- **EmailField**: Form field for email input with validation.
- **IntegerField**: Form field for integer input.

- **lback.forms.widgets_datetime**: Widgets for date and time input rendering.
- **DateInput**: Widget for date input.
- **DateTimeInput**: Widget for date and time input.

- **lback.forms.widgets**: General purpose form widgets.
- **TextInput**: Widget for single-line text input.
- **Textarea**: Widget for multi-line text input.
- **PasswordInput**: Widget for password input.
- **CheckboxInput**: Widget for checkbox input.
- **Select**: Widget for dropdown selection.

---

Models
------

The models module provides the Object-Relational Mapping (ORM) layer, based on SQLAlchemy, for interacting with the database.

- **lback.models**: Core module for database models.
- **AdminUser**: Model representing an administrative user.
- **Role**: Model for user roles.
- **Permission**: Model for defining user permissions.
- **BaseModel**: The base class for all application database models, providing common ORM functionalities.
- **DatabaseManager**: Manages database connections and sessions.
- **Product**: Example model for a product entity.
- **Session**: Model for managing user sessions in the database.
- **User**: Model representing a general application user.
- **Group**: Model for user groups.
- **UserPermission**: Model for managing individual user permissions.

---

Repositories
------------

The repository pattern abstracts data access logic, promoting cleaner code and testability.

- **lback.repositories**: Contains repositories for specific models.
- **AdminUserRepository**: Manages data access for AdminUser models.
- **PermissionRepository**: Manages data access for Permission models.
- **RoleRepository**: Manages data access for Role models.
- **UserRepository**: Manages data access for User models.

---

Security
--------

This module focuses on enhancing the application's security posture through various protection mechanisms.

- **lback.security**: Provides advanced security features.
- **AdvancedFirewall**: Implements a robust firewall for request filtering.
- **SecurityHeadersConfigurator**: Configures various security-related HTTP headers.
- **RateLimiter**: Limits the rate of requests to prevent abuse.
- **SQLInjectionProtection**: Provides tools for preventing SQL injection attacks.

---

Utilities
---------

The utils module offers a collection of helper functions and reusable tools to streamline common tasks across the framework.

- **lback.utils**: A diverse collection of utility functions.
- **AdminUserManager**: Manages administrative user-related operations.
- **AppSession**: Manages application-wide session functionalities.
- **EmailSender**: Provides functionalities for sending emails.
- **validate_uploaded_file, save_uploaded_file, delete_saved_file**: Helper functions for handling file uploads and storage.
- **file_extension_filter, split_filter, date_filter**: Utility functions for data filtering (possibly for templates or general use).
- **json_response (from lback.utils.response_helpers)**: Helper function for creating JSON responses.
- **SessionManager**: Manages user sessions, likely at a lower level than AppSession.
- **render, redirect, return_403, return_404, return_500, _get_model_form_data, paginate_query, json_response**: Shortcut functions for common view operations (rendering templates, redirects, error responses, etc.).
- **static, find_static_file (from lback.utils.static_files)**: Utilities for managing and serving static files.
- **path (from lback.utils.urls)**: Utility for defining URL paths.
- **UserManager**: Manages general user-related operations.
- **ValidationError (from lback.utils.validation)**: General validation exception.
- **PasswordValidator**: Validates password strength and format.
- **validate_json**: Validates JSON data against a schema or rules.

---

Commands
--------

The commands module provides a set of powerful command-line interface (CLI) tools to streamline various development and administrative tasks.

- **lback.commands**: CLI tools for project management.
- **AdminCommands**: CLI commands specific to admin functionalities.
- **AppCommands**: CLI commands for managing application components (e.g., creating new apps).
- **setup_database_and_defaults (from lback.commands.db_seed)**: CLI command or utility for seeding the database with initial data.
- **MigrationCommands**: CLI commands for database schema migrations.
- **ProjectCommands**: CLI commands for managing the overall project (e.g., creating new projects).
- **RunnerCommands**: CLI commands related to running the application server or other processes.
