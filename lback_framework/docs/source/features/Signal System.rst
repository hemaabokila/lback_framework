Signal System
=============

Lback Framework incorporates a Signal system based on a central SignalDispatcher.

This system provides a mechanism for decoupling components by allowing them to notify other parts of the application about events without needing direct references to the listeners.

This is useful for:

1. **Extensibility:** Allowing developers to hook into core framework events or application-specific events to add custom logic (e.g., sending emails on user registration, logging specific actions).

2. **Monitoring:** Listening to signals related to request lifecycle, errors, cache operations, etc., for logging, monitoring, and debugging purposes.

3. **Decoupling:** Keeping components independent of each other, as they only need to know how to send or receive signals, not directly call other components' methods.

How to Use:
-----------

**Access the Dispatcher:** The framework provides a single, globally accessible SignalDispatcher instance.

This instance is created early in the application's startup process and can be accessed by importing it ``from lback.core.dispatcher_instance``.

    .. code-block:: python

        # Example: Connecting a function to a signal
        from lback.core.dispatcher_instance import dispatcher # Access the dispatcher
        
        def my_custom_error_handler(sender, **kwargs):
            status = kwargs.get('status_code', 'N/A')
            path = getattr(kwargs.get('request'), 'path', 'N/A')
            print(f"Signal received from: {type(sender).__name__}, Status: {status}, Path: {path}")
        dispatcher.connect("error_response_generated", my_custom_error_handler)
        
* **Signals Emitted by the Framework:** The framework emits signals at various points, including:
* **Server Lifecycle:** server_starting, server_started, server_shutting_down, server_request_received, server_request_finished, server_response_sent.
* **Middleware Processing:** Signals related to the middleware chain and individual middleware execution.
* **Authentication/Authorization:** user_login_successful, user_login_failed, admin_login_successful, admin_login_failed, etc.
* **Database/ORM:** Signals related to database session management (via SQLAlchemy Middleware).
* **Cache Operations:** cache_item_set, cache_hit, cache_miss, cache_item_deleted.
* **Error Handling:** error_response_generated, unhandled_exception_response_generated.
* **Initialization:** Signals indicating when core components are initialized.

... and many more throughout the framework components.

By connecting your custom logic to these ``signals``, you can extend the framework's behavior without modifying its core code.

Refer to the documentation or component source code for a full list of available signals and the data they pass.
