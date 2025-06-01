.. _deployment:

Deployment
==========

Deploying your Lback application for production involves serving it with a **WSGI server**. Lback applications are built on the WSGI (Web Server Gateway Interface) standard, which defines how web servers communicate with web applications written in Python.

Choosing a WSGI Server
-----------------------

To run your Lback application in a production environment, you'll need a robust WSGI server. Some popular choices include:

* **Gunicorn (Green Unicorn)**: A widely used, pre-fork worker model HTTP server. It's known for its simplicity and good performance.
* **uWSGI**: A fast, self-healing, and developer-friendly application server. It's highly configurable and supports various protocols.

Basic Deployment Example (Gunicorn)
-----------------------------------

Let's look at a common deployment setup using Gunicorn. This assumes your Lback application's WSGI entry point is located in a ``wsgi.py`` file within your project structure, typically named ``application``.

To start your Lback application with Gunicorn, navigate to your project's root directory in your terminal and run:

.. code-block:: bash

   gunicorn myproject.wsgi:application

**Explanation:**

* ``gunicorn``: The command to invoke the Gunicorn server.
* ``myproject.wsgi``: This tells Gunicorn to look for the ``wsgi.py`` module inside your ``myproject`` package. Replace ``myproject`` with the actual name of your main project package.
* ``:application``: This specifies that the WSGI callable object within ``myproject.wsgi`` is named ``application``. This is the standard name for the WSGI entry point in many Python web frameworks.

Next Steps
----------

For a full production deployment, consider these additional steps:

* **Process Management**: Use a process manager like ``systemd``, ``Supervisor``, or `Docker` to ensure your WSGI server stays running and restarts automatically if it crashes.
* **Reverse Proxy**: Place a reverse proxy server (like Nginx or Apache) in front of your WSGI server. This handles static files, SSL termination, load balancing, and provides an additional layer of security.
* **Environment Variables**: Manage sensitive configurations (e.g., database credentials, secret keys) using environment variables, not directly in your code.
* **Worker Configuration**: Adjust the number of Gunicorn/uWSGI workers and threads based on your server resources and expected traffic.