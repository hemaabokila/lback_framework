"""
This file serves as the initialization point for the 'lback_framework/lback/models' package.
It is designed to expose the core components necessary for defining and managing the
application's data models within the Lback web framework. This package centralizes
the definition of database schemas, relationships between entities, and provides
utilities for interacting with the underlying database.

---

**Key Components Exposed by this Package:**

1.  **AdminUser, Role, Permission (from .adminuser):**
    These classes define the data models related to the administrative users and their
    access control within the application.

    * **AdminUser:** Represents an administrative user account, typically with elevated
        privileges for managing the application's backend.
    * **Role:** Defines a specific role that can be assigned to users (e.g., 'admin', 'editor').
        Roles are used to group permissions and simplify access control management.
    * **Permission:** Represents a specific action or resource that a user can be
        granted access to (e.g., 'can_edit_products', 'can_view_reports').

2.  **BaseModel (from .base):**
    The foundational base class for all data models within the Lback framework.
    This class typically provides common functionalities and attributes that all
    models share, such as primary key definitions, timestamp fields (created_at, updated_at),
    and potentially methods for common database operations.

3.  **DatabaseManager (from .database):**
    A component responsible for managing the database connection and session lifecycle.
    This class typically handles the initialization of the database engine, creation
    of database sessions, and other low-level database interactions, providing a
    centralized point for database access.

4.  **Product (from .product):**
    A specific data model representing a product within the application. This class
    defines the schema for product-related data, such as name, description, price,
    and other relevant attributes. It's an example of an application-specific model.

5.  **Session (from .session):**
    A data model representing a user's session. This class is used to store and
    manage session-specific data on the server side, enabling the application
    to maintain user state across multiple requests (e.g., login status, shopping cart).

6.  **User, Group, UserPermission (from .user):**
    These classes define the data models related to standard application users and
    their access control.

    * **User:** Represents a general user account within the application.
    * **Group:** Defines a group that users can belong to, often used to assign
        permissions or roles to multiple users collectively.
    * **UserPermission:** Represents a direct permission granted to a specific user,
        allowing for fine-grained access control beyond roles or groups.
"""
