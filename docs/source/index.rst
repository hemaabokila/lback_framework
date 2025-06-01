Welcome to lback documentation!
=================================

.. image:: _static/logo.png
   :align: center
   :width: 200px

**lback** is a modern and performant Python web framework designed with a focus on **modularity, control, and developer experience**. It offers a solid foundation for building a wide range of web applications, from simple APIs to complex, data-driven systems.

Key Features & Highlights:

* **Modular & Organized Architecture**: Enjoy a clean project structure inspired by popular frameworks like Django, making it easy to learn and scale with pluggable modules.
* **Powerful CLI (`manage.py`)**: A comprehensive command-line interface to streamline project, app, database, and user management tasks.
* **Flexible Configuration**: Load settings effortlessly from ``settings.py``, ``config.json``, and environment variables (``.env``).
* **Advanced Routing System**: Define clean, dynamic URL patterns with support for path variables and modular URL inclusion.
* **Robust Middleware Management**: Process requests and responses seamlessly before and after they reach your views, with built-in Dependency Injection support.
* **Strong ORM & Database Integration**: Full ``SQLAlchemy``_ support for efficient data modeling and interaction with various databases.
* **Automated Database Migrations**: Manage database schema changes in an organized and automated way using ``Alembic``_.
* **Comprehensive Authentication & Authorization**: Built-in support for Session-based and ``JWT``_ authentication, complemented by a flexible permissions system.
* **Efficient Templating**: Leverage the powerful ``Jinja2``_ templating engine for dynamic and reusable HTML interface rendering.
* **Smart Error Handling**: Catch errors gracefully and generate appropriate responses, with a built-in detailed error reporting system for development.
* **Essential Security Features**: Tools to safeguard your application against common vulnerabilities such as CSRF, CORS, SQL Injection, and XSS. Includes Rate Limiting and Security Headers.
* **Integrated Admin Panel**: A ready-to-use administrative interface featuring a Dashboard and comprehensive user management.
* **API Development Tools**: Helper utilities for building robust APIs, including data serialization capabilities.
* **Form Handling**: Streamline the creation and validation of HTML forms.
* **File Management**: Efficiently serve and manage both **Static Files** (CSS, JavaScript, images) and user-uploaded **Media Files**.
* **Signals System**: Enable decoupled components to communicate by allowing them to get notified when specific actions occur elsewhere in the framework.
* **Core Utilities**: Handy helper functions for common tasks related to sessions, users, emails, and more.
* **WSGI Support**: Optimized and ready for seamless deployment on production WSGI servers.
* **Integrated Testing**: First-class support for ``Pytest``_ to facilitate writing and running robust application tests.
* **Developer-Friendly Tools**: Includes built-in Logging and Debugging tools for a smoother development workflow.
* **Frontend Integration**: Optional styling capabilities with ``Tailwind CSS``_ integration.
* **Comprehensive Documentation**: Detailed API reference and developer guides to help you get started and build effectively.

.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _Alembic: https://alembic.sqlalchemy.org/en/latest/
.. _JWT: https://jwt.io/
.. _Jinja2: https://jinja.palletsprojects.com/en/latest/
.. _Pytest: https://docs.pytest.org/en/stable/
.. _Tailwind CSS: https://tailwindcss.com/

---

Getting Started
---------------

To get started with Lback, explore the following sections in order:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   features/Configuration System.rst

---

Core Features
-------------

These sections cover the fundamental building blocks of an Lback application:

.. toctree::
   :maxdepth: 2

   features/routing_system.rst
   features/Views & Responses.rst
   features/Templating System.rst
   features/Static Files.rst
   features/Media Files.rst
   features/file-uploads.rst
   features/Forms.rst

---

Data & Security
---------------

Learn how to manage your data and secure your application:

.. toctree::
   :maxdepth: 2

   features/Models & Database.rst
   features/Database Migrations System.rst
   features/Authentication.rst
   features/Authorization.rst
   features/sessions.rst
   features/Security Features.rst

---

Advanced & Integration Features
-------------------------------

Explore specialized functionalities and integration points:

.. toctree::
   :maxdepth: 2

   features/Admin Panel.rst
   features/API Tools.rst
   features/Signal System.rst
   features/Middleware System.rst
   features/custom_middlewares.rst
   features/logging_config.rst
   features/email-sender.rst
   features/validation_utilities.rst
   features/error_handling.rst
   features/Error Handling & Reporting.rst

---

Deployment
----------

Instructions on how to deploy your Lback application to production:

.. toctree::
   :maxdepth: 2

   features/Deployment.rst

---

Signals Reference
-----------------

Detailed documentation for all signals emitted throughout the framework, categorized by component:

.. toctree::
   :maxdepth: 2

   signals/api-signals.rst
   signals/admin-registry-signals.rst
   signals/admin-user.rst
   signals/admin-user-manager.rst
   signals/admin-user-repository.rst
   signals/auth.rst
   signals/error-handler.rst
   signals/middleware-manager.rst
   signals/migration_commands.rst
   signals/permission-repository.rst
   signals/role-repository.rst
   signals/session-manager.rst
   signals/template-renderer.rst
   signals/user-manager.rst
   signals/user-model.rst
   signals/user-repository.rst
   signals/wsgi-application.rst

---

API Reference & Project Structure
---------------------------------

Dive into the code and architecture of Lback:

.. toctree::
   :maxdepth: 2

   modules
   API Reference
   lback/lback

---

About
-----

The lback documentation is maintained and authored by Ibrahem Abo Kila, providing developers with detailed guidance and references for building with the framework.

**Author:** Ibrahem Abo Kila
**Email:** ibrahemabokila@gmail.com
**GitHub:** `https://github.com/hemaabokila/lback_framework <https://github.com/hemaabokila/lback_framework>`_
**LinkedIn:** `https://www.linkedin.com/in/ibrahem-abo-kila/ <https://www.linkedin.com/in/ibrahem-abo-kila/>`_
**YouTube:** `https://www.youtube.com/channel/UC... <https://www.youtube.com/@cryptodome22>`_