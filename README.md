# Lback Framework
![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)
<img src="lback/static/Logo.png" alt="Lback Logo" width="38"/>

**[Full Documentation](https://hemaabokila.github.io/lback-docs/)**

Lback A modern and powerful Python web framework aiming to accelerate web application development, focusing on structured architecture, scalability, and providing essential tools out-of-the-box.

## Table of Contents
- [Key Features](#key-features)
- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Create a New Project](#create-a-new-project)
  - [Project Structure (Brief)](#project-structure-brief)
  - [Run the Development Server](#run-the-development-server)
- [Detailed Project Structure](#detailed-project-structure)
  - [Project Root Folder](#project-root-folder)
  - [Apps Structure](#apps-structure)
- [Command-Line Interface (CLI)](#command-line-interface-cli)
  - [Using manage.py](#using-managepy)
  - [Command List](#command-list)
- [Configuration System](#configuration-system)
- [Routing System](#routing-system)
- [Views & Responses](#views--responses)
- [Models & Database](#models--database)
- [Database Migrations System](#database-migrations-system)
- [Middleware System](#middleware-system)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Templating System](#templating-system)
- [Error Handling & Reporting](#error-handling--reporting)
- [Signal System](#signal-system)
- [Security Features](#security-features)
- [Running Tests](#running-tests)
- [Built-in Admin Panel](#built-in-admin-panel)
- [API Tools](#api-tools)
- [Forms](#forms)
- [Static Files](#ftatic-files)
- [Media Files](#media-files)
- [Deployment](#deployment)
- [Full Documentation](#full-documentation)
- [About the Author / Contact](#about-the-author--contact)
- [License](#license)

## Key Features

Lback Framework offers a rich set of features to help you build robust web applications efficiently:

* **Modular Architecture** – Easily extendable with pluggable modules.
* **Organized Project Structure:** Follows a pattern similar to the popular Django framework for ease of learning and adoption.
* **Powerful Command-Line Interface (CLI):** A wide range of commands to manage your project, apps, databases, users, and more via `manage.py`.
* **Flexible Configuration System:** Load settings from `settings.py`, `config.json`, and environment variables (`.env`).
* **Advanced Routing System:** Define clean and dynamic URL patterns with support for path variables and including other URL files.
* **Middleware Management:** A robust structure for processing requests and responses before and after they reach the View, with support for Dependency Injection for middlewares.
* **Strong ORM Integration:** Full support for SQLAlchemy to efficiently manage data models and interact with databases.
* **Database Migrations System:** Utilize Alembic to manage database schema changes automatically and in an organized manner.
* **Authentication & Authorization:** Built-in support for Session-based and JSON Web Tokens (JWT) authentication, plus a flexible permissions system.
* **Efficient Templating System:** Uses the Jinja2 templating engine to render dynamic and reusable HTML interfaces.
* **Error Handling:** Catch errors and generate appropriate responses, with a built-in system for displaying detailed error reports in the browser during development.
* **Security Features:** Tools to protect against common vulnerabilities like CSRF, CORS, SQL Injection, and XSS, along with Rate Limiting and Security Headers.
* **Built-in Admin Panel:** A ready-to-use administrative system with a Dashboard and user management.
* **API Tools:** Helper tools for building Application Programming Interfaces (APIs), including data serialization.
* **forms**: Provides tools for creating and validating HTML forms.
* **Static Files:** Efficiently serves static assets like CSS, JavaScript, and images.
* **Media Files:** Manages user-uploaded media files
* **Signals System:** Allows decoupled applications to get notified when actions occur elsewhere in the framework.
* **Utilities** – Includes helper functions for sessions, users, emails, etc.
* **WSGI Support:** Ready for deployment on production WSGI servers.
* **Integrated Testing:** Support for Pytest to write and run application tests.
* **Other Development Tools:** built-in Logging and Debugging tools.
* **Debugging Tools** – Built-in tools for debugging and performance monitoring.
* **Tailwind CSS Integration** – Optional frontend styling with Tailwind CSS.
* **Documentation** – Comprehensive API documentation and developer guides.

## Installation

To install the Lback Framework, you can use pip:

```bash
pip install lback_framework
```
## Getting Started
Start your first project by following these simple steps.

### Create a New Project
Use the startproject command to create a new project structure:

```Bash
lback startproject myproject
```
Replace myproject with your desired project name.

### Project Structure (Brief)
A new folder named after your project (myproject) will be created containing the following basic structure (similar to Django's structure):
```bash
myproject/
├── manage.py           # Command-line utility for project management
├── myproject/          # Main project package folder
│   ├── __init__.py
│   ├── urls.py         # Main URL configurations
│   └── wsgi.py         # WSGI entry point for production deployment
└── .env                # Environment variables file (optional)
└── config.json         # Additional JSON format config file (optional)
└── settings.py         # Main settings file
```
### Run the Development Server
Navigate into your project folder and run the development server using the runserver command:

```Bash
python manage.py runserver
```
The server will typically run on http://127.0.0.1:8000/ by default.

## Detailed Project Structure
Lback Framework adopts an organized project structure to facilitate efficient development and component management.

### Project Root Folder
The project folder created by `startproject` contains the main files and configurations:
- `manage.py`: The project management script. Used to execute all CLI commands provided by the framework.
- `settings.py`: The main Python settings file for your project. This is where you define installed apps, database settings, Middlewares, etc.
- `urls.py`: The main URL configuration file. Here you define the root URL patterns and include URL patterns from different apps.
- `wsgi.py`: The entry point for your application when deployed using a WSGI server (like Gunicorn or uWSGI).
- `config.json`: An additional configuration file you can use for settings you prefer to keep in JSON format. It's loaded after .env and before `settings.py`.
- `.env`: A file for defining environment variables specific to your project (e.g., database connection details). It's loaded first.
### Apps Structure
Your project can be organized into separate applications (Apps) using the startapp command.

Each app represents a specific functional unit and has its own structure:
```bash
myproject/
└── myapp/  # App folder
    ├── __init__.py
    ├── admin.py      # Register models with the admin panel
    ├── models.py     # Define data models for the app (SQLAlchemy)
    ├── serializer.py # Serialization tools for API (if the app has API endpoints)
    ├── urls.py       # URL configurations for the app
    └── views.py      # Define View functions or classes that handle requests
```
## Command-Line Interface (CLI)
Lback Framework provides a `manage.py` script to manage your project from the command line.

### Using manage.py
To manage your project, navigate to the project folder in your terminal and execute commands using the following syntax:

```Bash
python manage.py <command> [arguments]
```
### Command List
Here is a list of commands available via `python manage.py`:



| Command             | Description                                                                 | Arguments                                      |
|---------------------|-----------------------------------------------------------------------------|------------------------------------------------|
| `startapp <name>`   | Creates a new app folder structure with the specified name.                 | `name`: The name for the new app.              |
| `runserver`         | Runs the local development server for your application.                     | None                                           |
| `makemigrations`    | Creates new database migration files based on changes in your Models.       | None                                           |
| `migrate`           | Applies pending database migrations.                                        | None                                           |
| `rollback <table>`  | Rolls back the last applied migration for a specific table.                 | `table`: The name of the table to rollback.    |
| `test`              | Runs all tests found in your project.                                       | None (Pytest options can be added)             |
| `collectstatic`     | Collects static files (CSS, JavaScript, Images) into a single folder.       | None                                           |
| `init_db`           | Initializes the database (typically used to create initial tables).         | None                                           |
| `create_superuser`  | Creates a superuser account for accessing the admin panel.                  | None (Prompts for username and password)       |
| `reset_password`    | Resets the password for an existing user.                                   | None (Prompts for user details)                |
| `deactivate_user`   | Deactivates an existing user account.                                       | None (Prompts for user details)                |
| `list_users`        | Lists all registered users in the system.                                   | None                                           |
| `activate_user`     | Activates a previously deactivated user account.                            | None (Prompts for user details)                |



## Configuration System
Lback Framework allows you to manage your project's settings with high flexibility.

Settings are loaded in the following order (later sources override earlier ones):

1. `.env` **file:** Environment variables from this file are loaded first.
2. `config.json` **file:** Settings from this JSON file are loaded.
3. `settings.py` **file:** Settings defined in this Python file are loaded (typically your main settings).

4. **Actual Environment Variables:** Environment variables defined in the operating system override all previous sources.

You can access settings anywhere in your application through the `config` object, typically made available via Dependency Injection.

## Routing System
URL configuration in Lback is usually done in `urls.py` files using a `urlpatterns` list.

You define patterns that map a URL path to a View function or class to handle the request.

```Python
# courses/urls.py
from lback.utils.urls import path
from .views import course_list_view

urlpatterns = [
    path("/courses/", course_list_view, allowed_methods=["GET"], name="course_list")
]
```
### URL Including
You can organize app-specific URLs in separate `urls.py` files and include them in the main URL configuration using the `include` function:

```Python
# myproject/urls.py
from lback.core.urls_utils import include

urlpatterns = [
    include('courses.urls', prefix='/'), # Include course URLs at the root path
    include('lback.admin.urls', prefix='/admin/'), # Include Admin URLs under the /admin/ prefix
    # ... other paths
]
```
## Views & Responses
Views are functions or classes that receive a `Request` object and return a `Response` object.

They are responsible for the logic of processing the request, interacting with Models and Templates, and generating the appropriate response.

```Python
# course/views.py
from lback.utils.shortcuts import render
from .models import Course

def course_list_view(request):
    db_session = request.db_session
    courses = db_session.query(Course).all()
    context = {
        "courses": courses, 
    }
    return render(request, "course_list.html", context)
```
The framework provides ready-to-use Response classes like `HTMLResponse`, `JSONResponse`, `RedirectResponse`, etc., to simplify response generation.

## Models & Database
Lback Framework supports database integration using SQLAlchemy as the ORM.

You define your data models as Python classes inheriting from SQLAlchemy's declarative base.

```Python
# courses/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from lback.models.base import BaseModel

class Course(BaseModel):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    image_path = Column(String(255), nullable=True)
    slug = Column(String(255), unique=True, nullable=True)

    def __str__(self):
        return self.name

    # ... relationships and other models
```
Database sessions are typically managed and provided to Views and other components via the SQLAlchemy Middleware and Dependency Injection.

## Database Migrations System
Using Alembic, you can manage database schema changes (adding tables, columns, modifying, deleting) in an organized and automated way.

- Use `python manage.py makemigrations` to create a new migration file based on your Model changes.
- Use `python manage.py migrate` to apply pending migrations to the database.
- Use `python manage.py rollback <table>` to roll back migrations for a specific table.
## Middleware System
Middlewares are components that process requests and responses in a chain before and after they reach the View.

They can be used for common tasks like authentication, logging requests, adding security headers, managing database sessions, and more.

The list of Middlewares is defined in your project's settings (typically in `settings.py`).

The framework provides a set of built-in Middlewares (as seen in the logs):

- `SQLAlchemySessionMiddleware`: Manages database sessions per request.
- `MediaFilesMiddleware`: Serves media files.
- `StaticFilesMiddleware`: Serves static files.
- `SessionMiddleware`: Manages user sessions.
- `FirewallMiddleware`: Acts as an internal firewall.
- `RateLimitingMiddleware`: Limits request rates.
- `SQLInjectionDetectionMiddleware`: Detects and prevents SQL injection.
- `BodyParsingMiddleware`: Parses and prepares request body data.
- `AuthMiddleware`: Handles authentication (Session and JWT).
- `CSRFMiddleware`: Provides protection against Cross-Site Request Forgery attacks.
- `CORSMiddleware`: Manages Cross-Origin Resource Sharing policies.
- `LoggingMiddleware`: Logs request and response details.
- `TimerMiddleware`: Measures and logs request response time.
- `DebugMiddleware`: Displays debugging information and request/response details during development.
- `SecurityHeadersMiddleware`: Adds HTTP security headers.

The framework also supports Dependency Injection in Middlewares, making it easy to access other components (like the Config, Loggers, Managers) from within a Middleware.

## Authentication
The framework provides a comprehensive and ready-to-use system for user management and **authentication**.

You can quickly integrate a full authentication flow into your application with minimal setup.
### Quick Setup for Authentication
To enable and configure the built-in authentication system, follow these simple steps:
#### 1- Create Authentication Templates:

The framework expects specific HTML templates for the authentication pages.

You just need to create these files in your `templates` directory (or wherever your framework is configured to look for templates):

* `register.html`: For user registration.
* `auth_login.html`: For user login.
* `request_password_reset.html`: For requesting a password reset link.
* `reset_password_confirm.html`: For setting a new password after a reset request.

These templates will automatically be rendered by the framework's internal authentication views, providing a consistent user experience.

#### 2- Add `auth_app` to `INSTALLED_APPS`:

Include the authentication application in your project's settings to enable its functionalities and ensure its views and models are loaded:
```python
# settings.py
INSTALLED_APPS = [
    # ... other apps ...
    'auth_app', # Include the built-in authentication application
]
```
#### 3- Include Authentication URLs:

Add the `auth_app` URLs to your project's main `urlpatterns`.

This makes all the necessary authentication endpoints (both web-based and API) accessible:
```python
# myproject/urls.py
from lback.core.urls_utils import include

urlpatterns = [
    include('lback.auth_app.urls', prefix='/auth/'),
    include('lback.admin.urls', prefix='/admin/'),
    # ... other project URLs ...
]
```
#### 4- Configure Email Settings (for Password Resets & Email Verification):
For features like password reset emails or email verification, you'll need to provide your SMTP server details in your `settings.py`:
```python
# settings.py
SMTP_SERVER = "smtp.gmail.com"  # Your SMTP server address
SMTP_PORT = 587                 # Your SMTP server port (e.g., 587 for TLS, 465 for SSL)
EMAIL_USERNAME = "your_email@example.com" # The email address for sending
EMAIL_PASSWORD = "your_app_password" # The password for the sending email (use app-specific passwords for security)
SENDER_EMAIL = "your_email@example.com" # The 'From' email address
USE_TLS = True                  # Set to True for TLS/SSL encryption
SENDER_NAME = "Your App Name"   # The sender name displayed in emails
```
This setup enables the framework to send transactional emails required for the authentication process.
### What the System Provides Automatically
Once configured, the framework's authentication system automatically handles:

* **Session-based Authentication:** Manages user sessions using cookies.
* **JWT Authentication:** Supports JSON Web Tokens for API authentication.
* **Secure Password Hashing:** Stores passwords securely using industry-standard hashing.
* **Pre-built Views & Endpoints:** Provides all necessary URL routes and underlying logic for registration, login, logout, email verification, and password reset (both web-based and API endpoints).
* **User Managers:** Utilizes internal helper classes (`UserManager`, `AdminUserManager`, `SessionManager`) for efficient user and session management.
## Authorization
Beyond authentication (verifying who a user is), **authorization** controls what an authenticated user is allowed to do.

The framework provides a flexible and robust system to define and enforce permissions, ensuring users can only access the resources and functionalities they are authorized for.

### 1- Permissions System: Role-Based Access Control (RBAC)
The core of the authorization system is built around a **Role-Based Access Control (RBAC)** model, allowing you to define granular permissions and organize them effectively.

* **`UserPermission` Model:** This model represents individual, distinct permissions (e.g., `blog.add_post`, `users.view_profile`, `admin.manage_settings`). You can define as many specific permissions as your application needs.

* **`Group` Model:** Groups act as roles.You can create groups (e.g., "Editors", "Moderators", "Managers") and assign a collection of `UserPermission` objects to each group.This simplifies permission management, as you assign users to groups rather than individually assigning many permissions to each user.
* **`User` Model:** Users are then assigned to one or more `Group` objects.A user inherits all permissions from the groups they belong to.The `User` model includes a robust `has_permission(permission_name: str) -> bool` method which efficiently checks if a user possesses a specific permission, considering their group memberships.
### Key Features:

* **Granular Control:** Define specific permissions that represent actions or access rights.
* **Superuser Bypass:** Users designated as "superusers" (typically by being part of an "admin" group or having an `is_superuser` flag) automatically bypass all permission checks, granting them full administrative access.
* **Efficient Checks:** The `has_permission` method on the `User` model uses caching to optimize performance, reducing database queries for frequently checked permissions.

### 2- Managing Permissions, Groups, and Users
The framework's **generic Admin Panel** provides a convenient interface for managing your authorization structure:
* **Adding Permissions:** Through the Admin Panel, you can define new `UserPermission` entries, giving them a unique name and an optional description. These represent the individual capabilities in your system.
* **Creating Groups:** You can create new `Group` objects (roles) and assign a name and description.
* **Assigning Permissions to Groups:** Crucially, the Admin Panel allows you to easily associate any defined `UserPermission` with specific `Group` objects. For example, you could create an "Editor" group and assign it `blog.add_post`, `blog.edit_post`, and `blog.delete_post permissions`.
* **Assigning Users to Groups:** Finally, you can assign individual `User` accounts to one or more `Group` objects. A user will then inherit all permissions from the groups they are a member of.

This integrated approach means you don't have to write custom code for basic permission management; it's all handled through the Admin Panel
### 3- Enforcing Authorization with `PermissionRequired` Decorator
The primary way to enforce authorization on your views is by using the `PermissionRequired`
**decorator**.

This decorator ensures that only users with the necessary permissions can access a particular view.
### How to Use:
You can apply the `PermissionRequired` decorator to your view functions or methods.

It accepts one or more permission strings:
* **Single Permission:**
```python
# myapp/views.py
from lback.auth.permissions import PermissionRequired
from lback.utils.shortcuts import render

@PermissionRequired("blog.view_posts")
def view_blog_posts(request):
    # This view requires the 'blog.view_posts' permission
    # ... fetch blog posts ...
    return render(request, "blog/list.html", {"posts": posts})
```
* **Multiple Permissions (User needs ALL of them):**
```python
# myapp/views.py
from lback.auth.permissions import PermissionRequired
from lback.utils.shortcuts import render

@PermissionRequired(["blog.add_post", "blog.publish_post"])
def create_and_publish_post(request):
    # This view requires BOTH 'blog.add_post' AND 'blog.publish_post' permissions
    # ... logic to create and publish a post ...
    return render(request, "blog/new_post_success.html")
```
* **Dynamic Permissions (Permissions based on request context):**
For more complex scenarios, you can provide a callable (a function) to `PermissionRequired`.
This function will receive the `request` object and should return the required permission(s) dynamically.
```python
# myapp/views.py
from lback.auth.permissions import PermissionRequired
from lback.utils.shortcuts import render

def get_dynamic_edit_permission(request):
    # Example: permission based on the type of user or object being edited
    if request.user and request.user.is_staff: # Assuming 'is_staff' property on User model
        return "article.edit_all"
    return "article.edit_own"

@PermissionRequired(get_dynamic_edit_permission)
def edit_article_view(request, article_id):
    # Permissions are determined by the 'get_dynamic_edit_permission' function at runtime
    # ... logic to edit an article ...
    return render(request, "articles/edit.html", {"article_id": article_id})
```
### 4- Permission Check Flow & Denied Access Handling
When a view decorated with `PermissionRequired` is accessed:

1. The framework attempts to retrieve the authenticated `user` object from the `request`.
2. If the user is a **superuser**, access is immediately granted.
3. Otherwise, the system calls the `user.has_permission()` method for each required permission.
4. If the user lacks any of the specified permissions, access is denied.
5. **Denied Access Handling:**
    * If the user is **not authenticated** at all, they are redirected to the login page (`/auth/login/`) with a flash message.
    * If the user is authenticated but **lacks the required permissions**, they are redirected to a 403 Forbidden page (`return_403`) with a flash message indicating denied access.
### 5- Signals for Authorization Flow
The authorization process also dispatches signals, allowing you to hook into the permission checking lifecycle for custom logic or logging:

* `permission_check_started`: Broadcast when a permission check begins.
    * **Sender:** `PermissionRequired` instance
    * **Kwargs:** `request`, `required_permissions` (set of permissions being checked), `user` (the user object), `view_func_name` (name of the view function).
* `permission_check_succeeded`: Broadcast when a user successfully passes a permission check.
    * **Sender:** `PermissionRequired` instance
    * **Kwargs:** `request`, `required_permissions`, `user`, `view_func_name`.
* `permission_check_failed`: Broadcast when a user fails a permission check.
    * **Sender:** `PermissionRequired` instance
    * **Kwargs:** `request`, `required_permissions`, `user`, `view_func_name`, `reason` (e.g., "user_not_authenticated", "permission_missing").

## Templating System
The framework uses the Jinja2 templating engine to render dynamic HTML pages.

Within your Views, you can use the `render` shortcut function (which leverages the `TemplateRenderer` available via Dependency Injection) to render templates:

```Python
# myapp/views.py
from lback.utils.shortcuts import render # Assuming 'render' is imported from framework shortcuts
from .models import Course
# ...

def course_list_view(request):
    db_session = request.db_session
    courses = db_session.query(Course).all()
    context = {
        "courses": courses, 
    }
    return render(request, "course_list.html", context) # Render the template
```
### How the `render` Shortcut Works
The `render` function simplifies template rendering by automatically handling common tasks.

It retrieves the `TemplateRenderer` from the request context and injects crucial data into your

template, such as:

- `request`: The incoming Request object.
- `current_user`: Information about the authenticated user.
- `session`: Session data.
- `config`: Your application's configuration.
- `csrf_token`: A token for Cross-Site Request Forgery (CSRF) protection.
- `static(path)`: A helper function to generate URLs for static files (e.g., CSS, JavaScript, images).

This approach ensures your templates have access to essential application data and security tokens without repetitive manual inclusion in every view.

### Example Template (`course_list.html`)
Here's how you might structure `course_list.html` to display the `courses` data passed from

the view:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Course List</title>
</head>
<body>
    <h1>All Courses</h1>
    <ul>
        {% for course in courses %}
            <li>{{ course.title }} - {{ course.created_at.strftime('%Y-%m-%d') }}</li>
        {% endfor %}
    </ul>
</body>
</html>
```
This setup provides a clear and concise way to build dynamic web pages using Jinja2 templates in your Lback Framework application.
## Error Handling & Reporting
The framework includes a mechanism to catch errors that occur during request processing and generate appropriate error responses (like 404 Not Found, 500 Internal Server Error).

During development, the framework features a browser error reporting system that provides a detailed report of the error (stack trace, request variables, project settings) to help you debug quickly.

You can customize these error pages using templates.

## Signal System


Lback Framework incorporates a Signal system based on a central SignalDispatcher.

This system provides a mechanism for decoupling components by allowing them to notify other parts of the application about events without needing direct references to the listeners.

This is useful for:

1. **Extensibility:** Allowing developers to hook into core framework events or application-specific events to add custom logic (e.g., sending emails on user registration, logging specific actions).

2. **Monitoring:** Listening to signals related to request lifecycle, errors, cache operations, etc., for logging, monitoring, and debugging purposes.

3. **Decoupling:** Keeping components independent of each other, as they only need to know how to send or receive signals, not directly call other components' methods.

### How to Use:

**Access the Dispatcher:** The framework provides a single, globally accessible SignalDispatcher instance.

This instance is created early in the application's startup process and can be accessed by importing it `from lback.core.dispatcher_instance`.

``` python
# Example: Connecting a function to a signal
from lback.core.dispatcher_instance import dispatcher # Access the dispatcher

def my_custom_error_handler(sender, **kwargs):
    status = kwargs.get('status_code', 'N/A')
    path = getattr(kwargs.get('request'), 'path', 'N/A')
    print(f"Signal received from: {type(sender).__name__}, Status: {status}, Path: {path}")
dispatcher.connect("error_response_generated", my_custom_error_handler)
```
* **Signals Emitted by the Framework:** The framework emits signals at various points, including:
* **Server Lifecycle:** server_starting, server_started, server_shutting_down, server_request_received, server_request_finished, server_response_sent.
* **Middleware Processing:** Signals related to the middleware chain and individual middleware execution.
* **Authentication/Authorization:** user_login_successful, user_login_failed, admin_login_successful, admin_login_failed, etc.
* **Database/ORM:** Signals related to database session management (via SQLAlchemy Middleware).
* **Cache Operations:** cache_item_set, cache_hit, cache_miss, cache_item_deleted.
* **Error Handling:** error_response_generated, unhandled_exception_response_generated.
* **Initialization:** Signals indicating when core components are initialized.

... and many more throughout the framework components.

By connecting your custom logic to these `signals`, you can extend the framework's behavior without modifying its core code.

Refer to the documentation or component source code for a full list of available signals and the data they pass.

## Security Features
In addition to authentication and authorization, the framework provides tools and components to contribute to securing your application:

- **CSRF Protection:** Protection against Cross-Site Request Forgery attacks via Middleware.
- **CORS Handling:** Managing Cross-Origin Resource Sharing policies via Middleware.
- **SQL Injection Protection:** Mechanisms (often integrated into the ORM and database interactions).
- **XSS Protection:** Tools to protect against Cross-Site Scripting attacks (perhaps via input sanitization or safe template rendering).
- **Rate Limiting:** Controlling the rate of incoming requests to protect against Denial of Service attacks.
- **Security Headers:** Adding security headers to responses to enhance browser security.
- **Firewall:** Potentially a basic application-level firewall system.
## Running Tests
The framework supports running tests using Pytest.

You can write tests for different code units (Views, Models, Utilities, etc.) and run them using the `manage.py` command:

```Bash
python manage.py test
```
## Built-in Admin Panel
Lback Framework comes with a ready-to-use administrative panel for managing your application's data models.

The Admin panel URLs are typically included under the `/admin/` prefix in the main URL configuration.

```Python
# myproject/urls.py
from lback.core.urls_utils import include

urlpatterns = [
    # ... other paths ...
    include('lback.admin.urls', prefix='/admin/'),
]
```
The Admin panel provides a graphical interface to add, modify, view, and delete data for models registered with it.

You can register your app's models with the admin panel via the app's `admin.py` file.

## API Tools
The framework provides a robust set of tools to assist you in building powerful and structured Application Programming Interfaces (APIs):

### Serialization:
The framework offers a dedicated Serializer component (found in `lback.api.serializer`).

This allows you to efficiently convert complex Python objects (like database models) into standard data formats such as JSON for API responses, and to parse incoming data from requests back into Python objects for validation and saving.

You can define various field types and create custom serializers.

**Example:** Defining a Model Serializer

Here's how you define a serializer for your `Course` model, allowing it to be easily converted to
and from JSON:
```python
# myapp/serializers.py
from lback.api.serializer import BaseModelSerializer
from .models import Course # Assuming your Course model is defined here

class CourseSerializer(BaseModelSerializer):
    class Meta:
        model = Course
        fields = '__all__' # This includes all fields from the Course model automatically
```

### API Views & Generic Views:
Beyond standard web views, the framework provides specialized **API Views** (from `lback.api.view`) and **Generic Views** (from `lback.api.generics`).

These views are designed to handle data-format requests and responses (typically JSON), offering a structured way to define your API endpoints.

The Generic Views provide pre-built functionality for common API operations (CRUD - Create, Read, Update, Delete), allowing you to write less code for standard endpoints.

**Example: Listing and Creating Courses API**

This example demonstrates how to create an API endpoint that lists all courses (`GET` request) using the `CourseSerializer` to format the output:
```python
# myapp/api_views.py
from lback.utils.response_helpers import json_response
from .models import Course
from .serializers import CourseSerializer # Import your serializer

def api_course_list_create_view(request):
    db_session = request.db_session

    if request.method == "GET":
        courses = db_session.query(Course).all()
        serializer = CourseSerializer(instance=courses, many=True)
        return json_response(serializer.data, status=200)
```
### API Documentation:
The framework includes tools for **API Documentation** (`lback.api.docs.APIDocs`).

This feature helps you automatically generate interactive and comprehensive documentation for your API endpoints, making it easier for consumers to understand and integrate with your API.

## Forms
The framework provides a powerful and flexible Forms system designed to handle HTML form rendering, data validation, and processing with ease.

It abstracts away common boilerplate, allowing you to focus on your application's logic.
### 1- Defining Forms
Forms are defined as Python classes that inherit from `lback.forms.forms.Form`.

You declare form fields as class attributes, and the framework's `FormMetaclass` automatically collects the
#### Example: A Simple Contact Form
Let's look at how you'd define a contact form:
```python
# myapp/forms.py
from lback.forms.fields import CharField, EmailField, IntegerField, BooleanField
from lback.forms.widgets import Textarea, CheckboxInput, PasswordInput
from lback.forms.forms import Form
from lback.forms.validation import ValidationError # For custom validation

class ContactForm(Form):
    """
    A simple form for contact inquiries.
    Demonstrates various field types and custom validation.
    """
    name = CharField(
        min_length=3,
        max_length=100,
        required=True,
        label="Your Name",
        help_text="Please enter your full name."
    )
    email = EmailField(
        required=True,
        label="Your Email"
    )
    age = IntegerField(
        min_value=18,
        max_value=99,
        required=False,
        label="Your Age",
        help_text="Must be between 18 and 99."
    )
    message = CharField(
        required=True,
        widget=Textarea(attrs={'rows': 5, 'cols': 40}), # Custom widget with HTML attributes
        label="Your Message"
    )
    newsletter_signup = BooleanField(
        required=False,
        label="Sign up for newsletter?",
        widget=CheckboxInput # Explicitly setting checkbox widget
    )
    password = CharField(
        required=False,
        widget=PasswordInput, # Renders as <input type="password">
        label="Password (optional)"
    )
    password_confirm = CharField(
        required=False,
        widget=PasswordInput,
        label="Confirm Password"
    )

    # You can add custom validation logic that applies to a single field
    def clean_name(self, value):
        """Custom validation for the 'name' field."""
        if "admin" in value.lower():
            raise ValidationError("Name cannot contain 'admin'.", code='invalid_name')
        return value

    # You can add custom validation logic that applies to the entire form (multiple fields)
    def clean(self):
        """
        Performs form-level validation.
        This method is called after individual field validations are complete.
        """
        # Always call the super().clean() to ensure base validations and initial clean_data.
        # This base clean() method already handles password mismatch, for example.
        super().clean() 
        
        # Access cleaned data from individual fields
        name = self.cleaned_data.get('name')
        email = self.cleaned_data.get('email')

        # Example of cross-field validation
        if name and email and name.lower() == email.split('@')[0].lower():
            raise ValidationError("Name cannot be the same as the email's local part.", code='name_email_match')
        
        return self.cleaned_data
```
### 2- Form Lifecycle & Usage
Working with forms typically involves these steps:
### a. Instantiating a Form
You can instantiate a form in two main ways:
* **Unbound Form (GET requests):** Used when initially displaying an empty form or a form pre-filled with initial data.
```python
# To display an empty form
form = ContactForm()

# To display a form with initial values (e.g., for editing an existing entry)
initial_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
form = ContactForm(initial=initial_data)
```
* **Bound Form (POST requests):** Used when processing submitted data from a user.

The `data` and `files` arguments should come directly from your request object (e.g., `request.POST`, `request.FILES`).
```python
# In your view handling a POST request
form = ContactForm(data=request.POST, files=request.FILES)
```
### b. Validating Form Data (`is_valid()`)
After instantiating a bound form, you must call the `is_valid()` method to trigger the validation process.

This method validates each field individually and then calls the form's `clean()` method for form-level validation.
```python
# In your view
form = ContactForm(data=request.POST)

if form.is_valid():
    # Form data is valid, access cleaned data
    name = form.cleaned_data['name']
    email = form.cleaned_data['email']
    # ... process data (e.g., save to database)
    return redirect('/success-page/')
else:
    # Form data is invalid, render the form again with errors
    # The template will use form.errors to display feedback
    return render(request, 'contact.html', {'form': form})
```
### c. Accessing Cleaned Data (`cleaned_data`)
If `is_valid()` returns `True`, the validated and converted data for each field is available in the `form.cleaned_data` property.

This dictionary contains the final, processed values ready for use (e.g., saving to a database).
```python
if form.is_valid():
    user_name = form.cleaned_data['name'] # This will be the cleaned string
    user_age = form.cleaned_data['age']   # This will be an integer, or None if not required
    # ...
```
### d. Handling Errors (`errors`, `non_field_errors`)
If `is_valid()` returns `False`, you can access the validation errors through:

* `form.errors`: A dictionary where keys are field names and values are lists of `ValidationError` objects for that field.It also contains the `__all__` key for form-level errors.
* `form.non_field_errors`: A convenient property that returns a list of errors that are not specific to any single field (i.e., errors from the `clean()` method).

You typically pass the form object back to your template to display these errors next to the relevant fields.
### 3- Field Types
The framework provides a variety of built-in field types to handle different kinds of data:

* `CharField`: For single-line text input.
    * **Options:** `min_length`, `max_length`.
* `EmailField`: Specifically for email addresses, includes email format validation.
* `IntegerField`: For whole numbers.
    * **Options:** `min_value`, `max_value`.
* `BooleanField`: For true/false values, typically rendered as checkboxes.
* `ChoiceField`: For selecting one option from a predefined set.
    * **Options:** choices (a list of tuples, e.g., `[('M', 'Male'), ('F', 'Female')]`).
* `DateField`: For dates.
* `TimeField`: For times.
* `DateTimeField`: For date and time.
* `FileField`: For file uploads.

All fields support common arguments:

* `required`: `True` by default. If `False`, the field can be left empty.
* `label`: The human-readable label for the field in the HTML form.
* `initial`: The initial value to populate the field with when the form is unbound.
* `help_text`: Explanatory text displayed next to the field.
* `widget`: Allows you to specify a custom HTML widget for the field.

### 4. Widgets
Widgets determine how a form field is rendered as HTML.

You can specify a custom widget using the `widget` argument when defining a field.
* `TextInput`: Default for `CharField`, `EmailField`, `IntegerField`.
* `Textarea`: For multi-line text input.
* `PasswordInput`: Renders an `<input type="password">` field.
* `CheckboxInput`: Renders an `<input type="checkbox">` field.
* `Select`: Renders a `<select>` dropdown for `ChoiceField`.
* `DateInput`: Renders an `<input type="date">` for `DateField`.
* `TimeInput`: Renders an `<input type="time">` for `TimeField`.
* `DateTimeInput`: Renders an `<input type="datetime-local">` for `DateTimeField`.
* `FileInput`: Renders an `<input type="file">` for `FileField`.
You can also pass `attrs` (attributes) to widgets to customize their HTML properties:
```python
message = CharField(
    widget=Textarea(attrs={'rows': 5, 'class': 'my-custom-textarea'}),
    label="Your Message"
)
```
Then, in your `contact.html` template, you can render the form using one of these methods:

* `{{ form.as_p }}`: Renders each field wrapped in `<p>` tags.
```html
<form method="post">
    {{ form.as_p }}
    <button type="submit">Submit</button>
</form>
```
* `{{ form.as_ul }}`: Renders each field wrapped in `<li>` tags, inside a `<ul>`.
```html
<form method="post">
    <ul>
        {{ form.as_ul }}
    </ul>
    <button type="submit">Submit</button>
</form>
```
* `{{ form.as_table }}`: Renders each field as a row (`<tr>`) in an HTML `<table>`.
```html
<form method="post">
    <table>
        {{ form.as_table }}
    </table>
    <button type="submit">Submit</button>
</form>
```
All rendering methods automatically include labels, input fields, error messages, and help text.

Non-field errors are displayed at the top of the form.
### 6- `ModelForm`: Connecting Forms to Database Models
`ModelForm` is a powerful tool within this framework, designed to simplify the creation of forms that interact directly with your database models (SQLAlchemy models).

Instead of manually defining each field in your form, `ModelForm` can automatically generate fields from your model's columns, saving you significant time and effort while reducing repetitive boilerplate code.

**When to Use `ModelForm`?**

Use `ModelForm` when you have a database model and want to create a form for entering new data for that model, or for editing existing model instances.

It's ideal for common CRUD (Create, Read, Update, Delete) operations related to your database entities.

**How to Define a `ModelForm`**

To define a `ModelForm`, you create a class that inherits `from lback.forms.models.ModelForm` and define an inner class named `Meta`.

Inside `Meta`, you must specify the database model that the form will operate on.

**Example: A Simple Product Form**

Let's use a `Product` model (assuming the content of `myapp/models/product.py` is as follows):
```python
# myapp/models/product.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"
```
Now, let's define the `ModelForm` for this model:
```python
# myapp/forms.py
from lback.forms.models import ModelForm
from lback.forms.fields import CharField # For adding non-model fields or overriding
from lback.forms.widgets import Textarea, TextInput # For customizing widgets
from lback.forms.validation import ValidationError # For custom validation
from lback.models.product import Product # Import your Product model

class ProductForm(ModelForm):
    class Meta:
        # Specify the database model this form will interact with
        model = Product

        # 'fields': A list of column names from the model to include in the form.
        # Fields for these columns will be automatically generated.
        fields = ['name', 'description', 'price', 'is_available', 'stock_quantity']

        # 'exclude': A list of column names from the model to exclude from the form.
        # If you specify 'fields', 'exclude' is ignored.
        # exclude = ['id', 'created_at']

        # 'widgets': A dictionary allowing you to specify a custom widget for a
        # particular field instead of its default widget.
        widgets = {
            'description': Textarea(attrs={'rows': 4, 'class': 'form-control-textarea'}),
            'name': TextInput(attrs={'placeholder': 'Enter product name'}),
        }

        # 'field_classes': (Advanced use) A dictionary allowing you to specify a custom
        # Field class for a particular field instead of the automatically generated one.
        # field_classes = {
        #     'name': CustomCharField # 'CustomCharField' would need to be defined
        # }

    # You can define additional fields here that don't directly correspond to model columns.
    # Note that these fields will NOT be automatically saved by form.save() to the model.
    # agreement = BooleanField(label="I agree to terms and conditions", required=True)

    # You can also override an automatically generated field from the model by defining it here.
    # For example, to increase the min_length for the 'name' field or change its label:
    # name = CharField(min_length=5, max_length=100, label="Product Title")

    # As with the base Form, you can add custom form-level validation logic here.
    def clean(self):
        """
        Performs form-wide validation.
        This method is called after individual field validations are complete.
        """
        # Always call super().clean() to ensure base validations are applied.
        super().clean()

        # Example of cross-field validation:
        # Ensure that the product price is not negative if it's available (hypothetical logic)
        price = self.cleaned_data.get('price')
        is_available = self.cleaned_data.get('is_available')

        if price is not None and price < 0 and is_available:
            self.add_error('price', ValidationError("Product cannot be available with a negative price.", code='invalid_price_availability'))
        
        return self.cleaned_data
```
**`ModelForm` Lifecycle & Usage**

Using a `ModelForm` follows the same lifecycle as the base `Form`, with a key added benefit: the ability to save data directly to your database.

**a. Instantiating a `ModelForm`**

* **Unbound Form:** Used to display an empty form or a form pre-filled with initial data.
```python
# To display an empty form for creating a new object
form = ProductForm()

# To display a form pre-filled with initial values (just like a regular Form)
initial_data = {'name': 'Sample Product', 'price': 10.99}
form = ProductForm(initial=initial_data)
```
* **Bound Form:** For processing submitted data (typically from a `POST` request).
```python
# In your view handling a POST request
# Make sure to pass request.form for data and request.files for file uploads
form = ProductForm(data=request.form, files=request.files)
```
* **Bound Form with an Existing Object (`instance`):** For modifying an existing database 

object. This is one of the most powerful features of `ModelForm`.

When you pass a model instance to the `instance` argument, the form will automatically populate its fields with that object's current values. When you then save the form, it will update this existing object instead of creating a new one.

```python
from lback.models.product import Product # Import your Product model
from lback.models.database import db_session # Assuming you have a db_session

# Retrieve an existing Product object from the database
existing_product = db_session.query(Product).get(product_id)

# To populate the form with the product's data and display it for editing
form = ProductForm(instance=existing_product)

# To process POST data for updating the product
form = ProductForm(data=request.form, files=request.files, instance=existing_product)
```
**b. Validating Form Data (`is_valid()`)**

Just like with `Form`, you must call `is_valid()` to trigger the validation process.

```python
# In your view
# ... (Obtain request.form and request.files data)
form = ProductForm(data=request.form, files=request.files)

if form.is_valid():
    # Data is valid; access it via form.cleaned_data
    product_name = form.cleaned_data['name']
    # ...
    # Now you can proceed to save the data
else:
    # Data is invalid; re-render the form with errors
    # Your template will use form.errors to display feedback
    return render(request, 'product_form.html', {'form': form})
```
**c. Accessing Cleaned Data (`cleaned_data`)**

Upon a successful `is_valid()` call, the validated, converted, and processed data for each field will be available in the `form.cleaned_data` property.

This dictionary contains the final values ready for use (e.g., saving to a database).

**d. Saving Data (`save()`)**

This is the core feature of `ModelForm`.

After successful validation, you can use the `save()` method to persist the data to your database.
```python
from sqlalchemy.orm import Session as DBSession # Ensure you import your DB session
from lback.core.response import Response # Assuming your Response object
import logging # For logging errors
logger = logging.getLogger(__name__)

# ... inside your view after form.is_valid() check
try:
    # If the form was initialized without an 'instance', save() will create a new Product object.
    # If the form was initialized with an 'instance', save() will update that existing object.
    
    # You MUST pass your SQLAlchemy session to the save() method.
    product_instance = form.save(db_session=db_session, commit=True) # commit=True is the default
    print(f"Product '{product_instance.name}' saved successfully!")
    return Response("Product saved successfully!", status=201) # Or redirect

except SQLAlchemyError as e:
    # Handle database-specific errors
    db_session.rollback() # Rollback any changes in case of a database error
    logger.error(f"Database error saving product: {e}", exc_info=True)
    return Response(f"Error saving product: {e}", status=500)
except Exception as e:
    # Handle unexpected general errors
    logger.exception(f"Unexpected error saving product: {e}")
    return Response(f"An unexpected error occurred: {e}", status=500)
```
* **commit argument:**

    * By default, `save()` will perform a `db_session.commit()` after adding/updating the object.

    * If you set `commit=False`, the object will be added/updated in the session but the changes will not be committed to the database.
This is useful if you need to perform additional operations on the object or session before the final commitment.
In this case, you will be responsible for calling `db_session.commit()` or `db_session.rollback()` yourself.
```python
# Example: Saving with commit=False for additional processing
if form.is_valid():
    product = form.save(db_session=db_session, commit=False)
    # Now you can make additional modifications to 'product'
    # or add other objects to the session
    # product.last_edited_by = request.user.id # Assuming you have a user in request
    db_session.add(product) # Re-add if detached or to re-confirm
    db_session.commit()
    return Response("Product saved and processed!", status=200)
```
**e. Handling File Fields (`FileField`) in `ModelForm`**

If your model includes a SQLAlchemy column of type `LargeBinary` (used for storing binary file data), `ModelForm` can automatically handle `FileFields`.

When a file is uploaded, `save()` will read the file's content, convert it to bytes, and store it in the LargeBinary column.
```python
# myapp/models/document.py (Example of a model storing files)
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(LargeBinary, nullable=False) # This column stores the binary file data
    original_filename = Column(String(255)) # To store the original file name
    size_bytes = Column(Integer) # To store the file size

# myapp/forms.py
from lback.forms.models import ModelForm
from lback.forms.fields import FileField # Make sure to import FileField
from lback.forms.validation import ValidationError
from lback.models.document import Document

class DocumentForm(ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'content'] # 'content' is your FileField

    def clean_content(self):
        """
        You can add file-specific validations here (e.g., file type, max size).
        """
        uploaded_file = self.cleaned_data.get('content')
        if uploaded_file:
            # You can access properties of the uploaded file
            if uploaded_file.size > 5 * 1024 * 1024: # 5MB limit
                raise ValidationError("File size exceeds 5MB.", code='file_too_large')
            
            # You can modify cleaned_data to add other file properties to your model
            self.cleaned_data['original_filename'] = uploaded_file.name
            self.cleaned_data['size_bytes'] = uploaded_file.size
        return uploaded_file
```

## Static Files
Static files are essential assets like CSS stylesheets, JavaScript files, and images that don't change dynamically.

framework efficiently serves these files to ensure fast loading times for your web application.

### Configuration
To properly serve static files, define their location in your project's `settings.py`:
```python
# settings.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_URL = '/static/' # The URL path for static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static') # The actual directory where static files are collected
STATIC_DIRS = [ # Additional directories to search for static files
    os.path.join(BASE_DIR, 'static'),
]
```
### Usage in Templates
Once configured, you can easily link to your static files within your Jinja2 templates using the `static` helper function, which is automatically injected into your template context by the `render` shortcut:
```html
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
```
## Media Files
Media files are user-uploaded content, such as profile pictures, document uploads, or video files.

framework provides tools to manage these dynamic assets, making it easy to store and serve user-generated content.
### Configuration
Set up the storage location and URL path for your media files in `settings.py`:
```python
# settings.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = 'media/uploads' # The directory where uploaded files will be stored
UPLOAD_URL = '/media/uploads/' # The URL path for accessing uploaded files

PROJECT_ROOT = BASE_DIR # Typically the same as BASE_DIR
```
### Usage in Templates
Similar to static files, you can reference your media files in templates.

If your model has a field storing the path to an uploaded file (e.g., `user.profile_picture_path`), you can construct the URL using the `UPLOAD_URL` from your settings or a helper function if available:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ user.username }} Profile</title>
</head>
<body>
    <h1>{{ user.username }}'s Profile</h1>
    {% if user.profile_picture_path %}
        <img src="{{ config.UPLOAD_URL }}{{ user.profile_picture_path }}" alt="Profile Picture" width="150">
    {% else %}
        <p>No profile picture uploaded.</p>
    {% endif %}
    
    <p>Bio: {{ user.bio }}</p>
</body>
</html>
```
## Deployment
An Lback application is a WSGI application.

To deploy it in a production environment, you need to use a compatible WSGI server (like Gunicorn or uWSGI) and point it to the entry point in your `wsgi.py` file.

```Bash

gunicorn myproject.wsgi:application
```
## Full Documentation
This file provides a quick overview of the Lback Framework.

For detailed information, examples, and in-depth explanations of all features and components, please visit the full documentation on the dedicated website:

[Lback Docs](https://hemaabokila.github.io/lback-docs/)
## About the Author / Contact

Lback Framework is developed by:

Name: Ibrahem Abokila

Email: ibrahemabokila@gmail.com

LinkedIn: https://www.linkedin.com/in/ibrahem-abo-kila/

YouTube Channel: https://www.youtube.com/@cryptodome22

For communication or inquiries, please use the contact details provided above.

## License
[LICENSE](LICENSE)
