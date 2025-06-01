Static Files
============

Static files are essential assets like CSS stylesheets, JavaScript files, and images that don't change dynamically.

framework efficiently serves these files to ensure fast loading times for your web application.

Configuration
-------------

To properly serve static files, define their location in your project's ``settings.py``:

    .. code-block:: python

        # settings.py
        import os

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        STATIC_URL = '/static/' # The URL path for static files
        STATIC_ROOT = os.path.join(BASE_DIR, 'static') # The actual directory where static files are collected
        STATIC_DIRS = [ # Additional directories to search for static files
            os.path.join(BASE_DIR, 'static'),
        ]

Usage in Templates
------------------

Once configured, you can easily link to your static files within your Jinja2 templates using the ``static`` helper function, which is automatically injected into your template context by the ``render`` shortcut:

    .. code-block:: html

        <!DOCTYPE html>
        <html>
        <head>
            <title>My Page</title>
            <link rel="stylesheet" href="{{ static('css/style.css') }}">
        </head>
        <body>
            <h1>Welcome!</h1>
            <img src="{{ static('images/logo.png') }}" alt="My Logo">
            
            <script src="{{ static('js/main.js') }}"></script>
        </body>
        </html>
        