"""
This file serves as the initialization point for the 'lback_framework/lback/core' package.
It is designed to expose the fundamental building blocks and core functionalities
of the Lback web framework. This package centralizes the definition and management
of the framework's internal mechanisms, including application control, request/response
handling, configuration, error management, routing, and server operations.

---

**Key Components Exposed by this Package:**

1.  **AppController (from .app_controller):**
    The central orchestrator of the Lback application. This class is responsible for
    managing the application lifecycle, dispatching requests to the appropriate handlers,
    and coordinating various framework components like middleware, routing, and response generation.
    It acts as the main entry point for processing incoming HTTP requests.

2.  **BaseMiddleware (from .base_middleware):**
    The foundational class for all middleware components within Lback. Middleware are
    components that process requests and responses before or after they reach the main
    application logic. This base class defines the interface and common behavior for
    custom middleware implementations.

3.  **Cache, CacheItem (from .cache):**
    Components for managing application-level caching.
    * **Cache:** Provides an interface for storing and retrieving data in a temporary,
        fast-access storage. It's used to reduce redundant computations or database queries.
    * **CacheItem:** Represents a single item stored within the cache, potentially including
        metadata like expiration times.

4.  **Configuration Management (from .config_manager and .config):**
    A set of utilities and classes for handling application configuration and settings.
    * **SettingsFileHandler:** Manages reading and writing application settings from configuration files.
    * **load_config:** A function to load the application's configuration from various sources.
    * **load_settings_module:** A function to load settings from a Python module.
    * **update_config:** A function to dynamically update configuration settings.
    * **start_settings_watcher:** Initiates a process to monitor configuration files for changes.
    * **sync_settings_to_config:** Synchronizes settings from a source to the active configuration.
    * **get_project_root:** A utility function to determine the root directory of the Lback project.
    * **Config:** The main class representing the application's configuration, holding all settings.

5.  **dispatcher (from .dispatcher_instance):**
    Likely a pre-initialized instance of a signal dispatcher or event manager. This component
    allows different parts of the framework (and application) to communicate with each other
    by sending and receiving signals or events, promoting a loosely coupled architecture.

6.  **ErrorHandler (from .error_handler):**
    Manages the handling and rendering of application errors and exceptions. This component
    intercepts unhandled exceptions, logs them, and generates appropriate error responses
    (e.g., custom error pages or JSON error messages) to the client.

7.  **Exceptions (from .exceptions):**
    A collection of custom exception classes specific to the Lback framework. These exceptions
    provide more granular control over error handling and allow for specific error responses
    based on the type of issue encountered.
    * **FrameworkException:** Base exception for all Lback framework-specific errors.
    * **Forbidden:** Raised when a user attempts to access a resource they are not authorized for (HTTP 403).
    * **HTTPException:** Base exception for all HTTP-related errors.
    * **BadRequest:** Raised for invalid client requests (HTTP 400).
    * **NotFound:** Raised when a requested resource or URL is not found (HTTP 404).
    * **RouteNotFound:** Specifically raised when no matching route is found for a URL.
    * **MethodNotAllowed:** Raised when an unsupported HTTP method is used for a route (HTTP 405).
    * **Unauthorized:** Raised when authentication is required but has failed or not been provided (HTTP 401).
    * **ConfigurationError:** Raised for issues related to application configuration.
    * **ValidationError:** Raised when data validation fails.
    * **ServerError:** Raised for internal server errors (HTTP 500).

8.  **setup_logging (from .logging_setup):**
    A function responsible for configuring the application's logging system. It sets up loggers,
    handlers, and formatters to ensure that application events, errors, and debugging information
    are captured and stored appropriately.

9.  **Middleware Management (from .middleware_loader and .middleware_manager):**
    Components for loading, creating, and managing middleware within the framework.
    * **load_middlewares_from_config:** Loads middleware definitions from the application configuration.
    * **create_middleware:** Instantiates a middleware class.
    * **import_class:** A utility function to dynamically import a Python class by its string path.
    * **MiddlewareManager:** Manages the execution order and application of multiple middleware components
        to incoming requests and outgoing responses.
    * **Middleware:** A class or interface representing a single middleware component.

10. **Response Handling (from .response):**
    Classes for constructing various types of HTTP responses.
    * **RedirectResponse:** Creates an HTTP redirect response.
    * **Response:** The base class for all HTTP responses.
    * **HTMLResponse:** Creates an HTTP response with HTML content.
    * **JSONResponse:** Creates an HTTP response with JSON content.

11. **Routing (from .router):**
    Components for defining and managing URL routing within the application.
    * **Route:** Represents a single route definition, mapping a URL pattern to a view handler.
    * **Router:** The central component responsible for matching incoming request URLs to the
        appropriate route and dispatching them to the corresponding view.

12. **Server (from .server):**
    Components related to running the Lback web server.
    * **Server:** The main class for the HTTP server, responsible for listening for incoming
        requests and handing them off to the application.
    * **initialize_core_components:** A function to initialize essential framework components
        before the server starts.
    * **wsgi_application:** The WSGI (Web Server Gateway Interface) application callable,
        which is the entry point for WSGI-compatible web servers.

13. **SignalDispatcher (from .signals):**
    A system for implementing signals (or events) within the framework. This allows
    different parts of the application to send notifications and react to them,
    promoting a decoupled architecture.

14. **Templates (from .templates):**
    Components for rendering HTML templates.
    * **TemplateRenderer:** The main class for rendering templates, often integrating with
        a templating engine (e.g., Jinja2).
    * **default_global_context:** Provides default variables or functions available
        to all templates.
    * **custom_uppercase:** A custom filter or function for template rendering.
    * **custom_url_tag:** A custom tag for generating URLs within templates.

15. **Type Definitions (from .types):**
    Custom type hints or definitions used throughout the framework for clarity and type checking.
    * **Request:** A type hint for the HTTP request object.
    * **HTTPMethod:** An enumeration or type hint for HTTP methods (GET, POST, etc.).
    * **TypeConverter:** A base class or type for URL path converters.
    * **UploadedFile:** A type hint for objects representing uploaded files.
    * **UUIDConverter:** A URL path converter specifically for UUIDs.
    * **IntegerConverter:** A URL path converter specifically for integers.

16. **URL Utilities (from .urls_utils):**
    Utilities for managing URL patterns.
    * **Include:** A function or class to include URL patterns from other modules,
        allowing for modular URL configuration.

17. **WebSocketServer (from .websocket):**
    A component for handling WebSocket communication, enabling real-time,
    bidirectional communication between the server and clients.

18. **WSGI Entry Point (from .wsgi_entry):**
    Utilities related to the WSGI application setup.
    * **create_wsgi_app:** A function to create the WSGI application instance.
    * **setup_logging:** A function to configure logging specifically for the WSGI environment.
"""