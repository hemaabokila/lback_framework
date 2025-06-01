Logging Configuration
=====================

The Lback framework provides a flexible logging system that you can easily configure to suit your application's needs, especially during development and production. You have direct control over the **logging level** and how logs are displayed based on your application's **debug mode**.

---

Controlling Logging Level with ``DEBUG`` and ``LOGGING_LEVEL``
--------------------------------------------------------------

The logging behavior is primarily driven by two settings in your application's ``Config`` (or ``settings.py`` file):

1.  **DEBUG**: This boolean setting is central to your application's operational mode.

    * When ``DEBUG = True``: The logging system defaults to a more verbose output, typically ``INFO`` level, unless explicitly overridden. This is ideal for development, as it provides detailed insights into the application's flow.
    * When ``DEBUG = False``: The logging system automatically raises its effective level to ``WARNING`` to minimize unnecessary log output in production environments. This helps keep log files manageable and focuses on significant issues.

2.  **LOGGING_LEVEL**: This string setting allows you to specify a global minimum logging level for your application. Common values include:

    * ``"DEBUG"``: For highly granular debugging information.
    * ``"INFO"``: For general informational messages, indicating the normal operation of the system.
    * ``"WARNING"``: For indicating potential issues that don't prevent the application from running but should be noted.
    * ``"ERROR"``: For indicating errors that prevent some functionality from working correctly.
    * ``"CRITICAL"``: For severe errors that indicate the application might be in a critical state.

**How they interact:**

The ``setup_logging`` function in the framework intelligently combines these two settings:

* If ``DEBUG`` is ``True``, the logging level will be ``LOGGING_LEVEL`` (e.g., ``"INFO"``, ``"DEBUG"``). If ``LOGGING_LEVEL`` isn't set, it defaults to ``"INFO"``. This means you can get detailed logs when debugging.
* If ``DEBUG`` is ``False``, the logging level will be **forced to at least** ``"WARNING"``, regardless of what ``LOGGING_LEVEL`` is set to. This ensures that only important warnings and errors are logged in production, preventing log floods.

**Example Configuration in** ``settings.py`` **(or** ``Config`` **):**

.. code-block:: python

    # settings.py (or your Config class)

    DEBUG = True  # Set to True for development/debugging
    LOGGING_LEVEL = "DEBUG" # You can set this to INFO, WARNING, ERROR, etc.

    # Optional: More advanced logging configuration (see below)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO', # This level will be overridden by setup_logging
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO', # This level will also be overridden by setup_logging
        },
        'loggers': {
            'lback': { # Example for framework-specific logger
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            # You can define loggers for your own apps here
            'myapp': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
        }
    }

In the example above, if ``DEBUG`` is ``True`` and ``LOGGING_LEVEL`` is ``"DEBUG"``, the console handler and root logger would effectively log at ``DEBUG`` level. If ``DEBUG`` were ``False``, they would be forced to ``WARNING`` level, regardless of ``LOGGING_LEVEL``.

---

Advanced Logging with ``LOGGING`` Dictionary
--------------------------------------------

For more granular control over your logging setup (e.g., multiple handlers, different formats, file logging), you can define a ``LOGGING`` dictionary in your ``Config``. The framework uses Python's ``logging.config.dictConfig`` to apply this configuration.

Even when using a ``LOGGING`` dictionary, the ``setup_logging`` function ensures that the ``DEBUG`` and ``LOGGING_LEVEL`` settings correctly influence the **effective minimum level** for your console handler and root logger. This means you can define elaborate logging configurations, but still rely on ``DEBUG`` to easily toggle between verbose development logging and concise production logging.

If your ``LOGGING`` dictionary isn't found or if there's an error applying it, the framework gracefully falls back to a basic console logging configuration to ensure you still get some log output.

By leveraging these settings, you maintain precise control over your application's logging verbosity, crucial for both effective debugging and efficient production monitoring.