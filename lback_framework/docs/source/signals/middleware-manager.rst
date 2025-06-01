.. _middleware-manager-signals:

Signals from MiddlewareManager
==============================

The :py:class:`lback.core.middleware.MiddlewareManager` orchestrates the execution of middleware components for both incoming requests and outgoing responses. This class emits a comprehensive set of signals throughout the middleware processing chain, providing **deep insights into request/response flow, enabling custom logging, performance monitoring, and advanced debugging capabilities.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``middleware_manager_initialized``
     - Emitted immediately after the :py:class:`~lback.core.middleware.MiddlewareManager` instance has been successfully initialized.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The instance of the middleware manager.
   * - ``middleware_added``
     - Emitted when a new middleware instance is successfully added to the manager's chain.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The middleware object that was added.<br>``middleware_name`` (:py:class:`str`): The class name of the added middleware.
   * - ``middleware_add_failed``
     - Emitted when an attempt to add a middleware fails (e.g., if the object does not implement the Middleware Protocol).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`Any`): The object that failed to be added.<br>``middleware_name`` (:py:class:`str`): The class name of the failed middleware.<br>``error_type`` (:py:class:`str`): A string indicating the reason for failure (e.g., "invalid_type").
   * - ``middleware_removed``
     - Emitted when a specific middleware instance is successfully removed from the manager.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The middleware object that was removed.<br>``middleware_name`` (:py:class:`str`): The class name of the removed middleware.
   * - ``middleware_remove_failed``
     - Emitted when an attempt to remove a specific middleware instance fails (e.g., if the instance was not found).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The middleware object that failed to be removed.<br>``middleware_name`` (:py:class:`str`): The class name of the failed middleware.<br>``error_type`` (:py:class:`str`): A string indicating the reason for failure (e.g., "not_found").
   * - ``middleware_removed_by_class``
     - Emitted when one or more instances of a specific middleware class are successfully removed from the manager.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_class`` (:py:class:`Type`[:py:class:`~lback.core.middleware.Middleware`]): The class of the middlewares that were removed.<br>``middleware_class_name`` (:py:class:`str`): The name of the middleware class.<br>``removed_count`` (:py:class:`int`): The number of instances removed.<br>``removed_instances`` (:py:class:`list` of :py:class:`~lback.core.middleware.Middleware`): A list of the actual middleware instances that were removed.
   * - ``middleware_remove_by_class_failed``
     - Emitted when an attempt to remove middlewares by class fails (e.g., if an invalid class type is provided).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_class`` (:py:class:`Type`[:py:class:`~lback.core.middleware.Middleware`]): The class that failed to be removed.<br>``middleware_class_name`` (:py:class:`str`): The name of the middleware class.<br>``error_type`` (:py:class:`str`): A string indicating the reason for failure (e.g., "invalid_type").
   * - ``middleware_request_processing_started``
     - Emitted at the very beginning of the entire `process_request` middleware chain for an incoming request.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``request`` (:py:class:`Any`): The incoming request object.<br>``method`` (:py:class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.
   * - ``middleware_process_request_started``
     - Emitted just before an individual middleware's `process_request` method is called.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The specific middleware instance whose `process_request` method is about to be called.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The current state of the request object.
   * - ``middleware_process_request_succeeded``
     - Emitted after an individual middleware's `process_request` method has successfully executed and returned `None` (indicating the chain should continue).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The specific middleware instance that completed successfully.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The request object after being processed by this middleware.
   * - ``middleware_process_request_failed``
     - Emitted when an individual middleware's `process_request` method fails (e.g., raises an exception or returns an invalid response type).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The specific middleware instance that failed.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The request object at the time of failure.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "invalid_response_type", "exception").<br>``returned_type`` (:py:class:`Type`[:py:class:`Any`], *optional*): The unexpected type returned by the middleware, if applicable.<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an exception.
   * - ``middleware_request_short_circuited``
     - Emitted when a middleware's `process_request` method returns a `Response` object, effectively stopping the middleware chain and preventing the request from reaching the view.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The middleware instance that short-circuited the request.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The request object at the time of short-circuit.<br>``response`` (:py:class:`~lback.core.response.Response`): The response object returned by the middleware.
   * - ``middleware_request_processing_finished``
     - Emitted after the entire `process_request` middleware chain has completed, and the request is about to proceed to the view (or was short-circuited earlier).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``request`` (:py:class:`Any`): The final state of the request object.<br>``method`` (:py:class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.
   * - ``middleware_response_processing_started``
     - Emitted at the very beginning of the entire `process_response` middleware chain for an outgoing response.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``request`` (:py:class:`Any`): The incoming request object.<br>``method`` (:py:class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.<br>``initial_response`` (:py:class:`~lback.core.response.Response`): The response object generated by the view or a short-circuiting middleware.
   * - ``middleware_process_response_started``
     - Emitted just before an individual middleware's `process_response` method is called.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The specific middleware instance whose `process_response` method is about to be called.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The request object.<br>``current_response`` (:py:class:`~lback.core.response.Response`): The response object as it stands before this middleware processes it.
   * - ``middleware_process_response_succeeded``
     - Emitted after an individual middleware's `process_response` method has successfully executed.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The specific middleware instance that completed successfully.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The request object.<br>``processed_response`` (:py:class:`~lback.core.response.Response`): The response object after being processed by this middleware.
   * - ``middleware_process_response_failed``
     - Emitted when an individual middleware's `process_response` method fails (e.g., raises an exception or returns an invalid response type).
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``middleware_instance`` (:py:class:`~lback.core.middleware.Middleware`): The specific middleware instance that failed.<br>``middleware_name`` (:py:class:`str`): The class name of the middleware.<br>``request`` (:py:class:`Any`): The request object.<br>``current_response`` (:py:class:`~lback.core.response.Response`): The response object at the time of failure.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "invalid_response_type", "exception").<br>``returned_type`` (:py:class:`Type`[:py:class:`Any`], *optional*): The unexpected type returned by the middleware, if applicable.<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an exception.
   * - ``middleware_response_processing_finished``
     - Emitted after the entire `process_response` middleware chain has completed, and the final response is ready to be sent back to the client.
     - ``sender`` (:py:class:`~lback.core.middleware.MiddlewareManager`): The middleware manager instance.<br>``request`` (:py:class:`Any`): The request object.<br>``method`` (:py:class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.<br>``final_response`` (:py:class:`~lback.core.response.Response`): The final response object after all response middlewares have been applied.