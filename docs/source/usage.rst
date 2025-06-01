Usage
=====

This section explains how to use the **lback** framework to build and manage your applications.

---

Creating a New Project
----------------------

To create a new Lback project:

.. code-block:: bash

    lback createproject myproject

Replace ``myproject`` with your desired project name. This command sets up a new directory structure for your project, including all necessary files and boilerplate code.

The new project will include:

.. code-block:: bash

    myproject/
    ├── manage.py           # Command-line utility for project management
    ├── myproject/          # Main project package folder
    │   ├── __init__.py
    │   ├── urls.py         # Main URL configurations
    │   └── wsgi.py         # WSGI entry point for production deployment
    ├── .env                # Environment variables file (optional)
    ├── config.json         # Additional JSON format config file (optional)
    └── settings.py         # Main settings file

---

App Management
--------------

You can create a new app within your project:

.. code-block:: bash

    python manage.py startapp myapp

Replace ``myapp`` with your desired app name. This command creates a new directory structure for your app within the project, pre-filled with essential files.

The new app will include:

.. code-block:: bash

    myproject/
    └── myapp/              # App folder
        ├── __init__.py
        ├── admin.py        # Register models with the admin panel
        ├── models.py       # Define data models for the app (SQLAlchemy)
        ├── serializer.py   # Serialization tools for API (if the app has API endpoints)
        ├── urls.py         # URL configurations for the app
        └── views.py        # Define View functions or classes that handle requests

---

Database Management & Migrations
--------------------------------

Lback leverages database migrations to manage changes to your database schema as your application evolves.

* **Create New Migration Files:**
    Scans your models for changes and generates new migration scripts.

    .. code-block:: bash

        python manage.py makemigrations

* **Apply Database Migrations:**
    Applies all pending migration scripts to update your database schema to the latest version.

    .. code-block:: bash

        python manage.py migrate

* **Rollback Migrations for a Table:**
    Reverts migrations for a specific database table to a previous state. Replace ``<table>`` with the actual table name.

    .. code-block:: bash

        python manage.py rollback <table>

* **Initialize the Database:**
    Sets up the initial database schema and seeds it with any default data required for your application.

    .. code-block:: bash

        python manage.py init_db

---

Admin and User Management
-------------------------

Lback provides a robust command-line interface for managing users and the admin panel.

* **Create a Superuser:**
    Initiates an interactive prompt to create a new administrative superuser account, granting full access to the admin dashboard.

    .. code-block:: bash

        python manage.py createsuperuser

    *Login to the admin dashboard via `/admin/` in your browser using your superuser credentials.*

* **Reset a User's Password:**
    Resets the password for an existing user.

    .. code-block:: bash

        python manage.py reset_password

* **Deactivate a User:**
    Disables a user's account, preventing them from logging in.

    .. code-block:: bash

        python manage.py deactivate_user

* **List All Users:**
    Displays a comprehensive list of all registered user accounts in the system.

    .. code-block:: bash

        python manage.py list_users

* **Activate a User:**
    Re-enables a previously deactivated user account.

    .. code-block:: bash

        python manage.py activate_user

---

Server and Development Utilities
--------------------------------

These commands assist with running your development server and other crucial development tasks.

* **Run the Development Server:**
    Starts the Lback development server. By default, it runs on ``http://127.0.0.1:8000``.

    .. code-block:: bash

        python manage.py runserver

* **Run Tests:**
    Executes the entire test suite configured for your Lback project.

    .. code-block:: bash

        python manage.py test

* **Collect Static Files:**
    Gathers static files (CSS, JavaScript, images, etc.) from all your applications and copies them into a single directory, typically for efficient serving in production environments.

    .. code-block:: bash

        python manage.py collectstatic