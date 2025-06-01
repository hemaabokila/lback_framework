"""
This file serves as the initialization point for the 'lback_framework/lback/repositories' package.
It is designed to expose the core components necessary for implementing the repository pattern
within the Lback web framework. This package centralizes the definition and management of
data access logic, providing an abstraction layer over the database for specific models.
It encapsulates the mechanisms for retrieving, storing, and querying data, promoting a
clean separation of concerns between the application's business logic and data persistence.

---

**Key Components Exposed by this Package:**

1.  **AdminUserRepository (from .admin_user_repository):**
    A repository class specifically designed for interacting with AdminUser data.
    This component provides methods for performing CRUD (Create, Read, Update, Delete)
    operations on administrative user records, abstracting away the direct database
    interactions for AdminUser models. It might include specialized queries
    relevant to admin user management.

2.  **PermissionRepository (from .permission_repository):**
    A repository class dedicated to managing Permission data. This component offers
    methods for accessing, creating, updating, and deleting permission records. It
    ensures that permission-related database operations are handled consistently
    and efficiently, supporting the application's authorization system.

3.  **RoleRepository (from .role_repository):**
    A repository class focused on handling Role data. This component provides
    methods for performing CRUD operations on role records, which are used to
    group permissions and assign them to users. It centralizes the data access
    logic for roles, supporting the role-based access control (RBAC) system.

4.  **UserRepository (from .user_repository):**
    A repository class specifically designed for interacting with standard User data.
    This component provides methods for performing CRUD operations on general user
    records, abstracting away the direct database interactions for User models.
    It might include specialized queries for user authentication, profile management,
    or other user-centric operations.
"""