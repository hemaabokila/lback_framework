.. _wsgi-application-signals:

Signals from WSGI Application and Server
========================================

The WSGI application entry point (`wsgi_application`) and the main :py:class:`lback.core.server.Server` class are crucial components in the application's lifecycle, handling incoming requests and managing the server. They emit signals at various stages, providing **comprehensive hooks for monitoring server health, tracking request flow, handling initialization errors, and integrating with external logging and performance measurement tools.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``wsgi_application_error``
     - Emitted when the WSGI application encounters a critical error preventing request processing, typically due to core framework components not being initialized.
     - ``sender`` (:py:class:`str`): Always "wsgi_application".<br>``error_type`` (:py:class:`str`): Describes the type of initialization error (e.g., "core_components_not_initialized").<br>``environ`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The WSGI environment dictionary.
   * - ``server_request_received``
     - Emitted immediately after a new request is received by the WSGI application, before any significant processing begins (e.g., Request object creation).
     - ``sender`` (:py:class:`str`): Always "wsgi_application".<br>``method`` (:py:class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.<br>``full_path`` (:py:class:`str`): The full path including query string.<br>``headers`` (:py:class:`Dict`[:py:class:`str`, :py:class:`str`]): A dictionary of HTTP request headers.<br>``environ`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The raw WSGI environment dictionary.
   * - ``server_request_finished``
     - Emitted at the very end of the WSGI application's request processing, just before the final response is returned to the WSGI server. Includes performance metrics.
     - ``sender`` (:py:class:`str`): Always "wsgi_application".<br>``method`` (:py:class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.<br>``full_path`` (:py:class:`str`): The full path including query string.<br>``duration`` (:py:class:`float`): The total time taken to process the request in seconds.<br>``status_code`` (:py:class:`int` or :py:class:`str`): The HTTP status code of the final response (or 'N/A' if unavailable).<br>``response`` (:py:class:`~lback.core.response.Response`, *optional*): The final response object generated.<br>``request`` (:py:class:`~lback.core.types.Request`, *optional*): The request object that was processed.