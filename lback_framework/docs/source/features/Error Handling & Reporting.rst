Error Handling & Reporting
==========================

The Lback framework provides a robust and flexible system for handling errors that occur during your application's request processing. This ensures a graceful user experience even when unexpected issues arise, while offering powerful debugging tools for developers.

---

How Error Handling Works
------------------------

The core of the error handling system is the **ErrorHandler** class. This class is responsible for catching exceptions and HTTP errors (like 404 Not Found or 500 Internal Server Error) and generating appropriate responses.

Key aspects of its operation include:

* **Dedicated Handlers:** The ``ErrorHandler`` has specific methods to deal with common HTTP errors:

    * **handle_404**: For resources that are not found.
    * **handle_403**: For forbidden access attempts (e.g., permission denied).
    * **handle_405**: For HTTP methods not allowed on a given URL.
    * **handle_500**: For explicit internal server errors.
    * **handle_exception**: A comprehensive handler for any unhandled exceptions that occur during view execution or other parts of the request lifecycle.
    * **handle_custom_error**: For rendering errors with specific custom status codes and messages.

* **Integration with Shortcuts:** For convenience, the framework provides shortcut functions like ``return_404()``, ``return_403()``, and ``return_500()`` which internally delegate to the ``ErrorHandler``, ensuring consistent error response generation.

* **Signals Integration:** The ``ErrorHandler`` dispatches signals (e.g., ``error_response_generated``, ``unhandled_exception_response_generated``) at various stages of error handling. This allows you to hook into the error flow for custom logging, monitoring, or notification purposes.

---

Debugging with Browser Error Reporting
--------------------------------------

One of the most valuable features for developers is the framework's **browser error reporting system**, which is active when your application is running in **DEBUG mode**.

When ``DEBUG`` is set to ``True`` in your ``Config`` (or ``settings.py``), and an error or exception occurs, the framework will render a detailed HTML page directly in the browser instead of a generic error message. This debug page includes:

* **Detailed Stack Trace:** A full traceback of the error, pinpointing exactly where the exception occurred in your code.
* **Request Variables:** Information about the incoming HTTP request, including method, path, headers, and body (if applicable).
* **Context Variables:** For template rendering errors (like ``TemplateNotFound``), the context variables that were available to the template are displayed.
* **Router Information:** For 404 errors, a list of available routes might be displayed to help identify routing issues.
* **Sensitive Data Masking:** (Implicitly, if implemented in ``Config`` or rendering) While in debug mode, be cautious about exposing sensitive data in error pages in a production-like environment.

This detailed reporting significantly speeds up the debugging process by providing all necessary information directly in your browser.

---

Customizing Error Pages with Templates
--------------------------------------

The framework allows you to customize the appearance and content of these error pages by creating your own HTML templates.

The ``ErrorHandler`` attempts to render specific debug templates first if ``DEBUG`` is ``True``. If those templates are not found or if ``DEBUG`` is ``False``, it falls back to a generic HTML response.

You can create these templates in your configured template directories:

* **debug_404.html**: Custom template for 404 Not Found errors when ``DEBUG`` is ``True``.
* **debug_403.html**: Custom template for 403 Forbidden errors when ``DEBUG`` is ``True``.
* **debug_405.html**: Custom template for 405 Method Not Allowed errors when ``DEBUG`` is ``True``.
* **debug_error.html**: Custom template for unhandled exceptions (500 errors) when ``DEBUG`` is ``True``.

If these debug-specific templates are not provided, or if the framework is not in ``DEBUG`` mode, a simple, generic HTML response will be returned for these error codes. For ``handle_500`` (explicitly raised 500) and ``handle_custom_error``, there's no specific debug template; they default to their generic HTML output.

By providing custom error templates, you can ensure that your application maintains a consistent look and feel even when errors occur, and you can provide more user-friendly messages for production environments.