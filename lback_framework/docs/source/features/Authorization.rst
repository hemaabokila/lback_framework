Authorization
=============

Beyond authentication (verifying who a user is), **authorization** controls what an authenticated user is allowed to do.

The framework provides a flexible and robust system to define and enforce permissions, ensuring users can only access the resources and functionalities they are authorized for.

---

1. Permissions System: Role-Based Access Control (RBAC) for Standard Users
-------------------------------------------------------------------------

The core of the **standard user authorization system** is built around a **Role-Based Access Control (RBAC)** model, allowing you to define granular permissions and organize them effectively for your application's regular users.

* **``UserPermission`` Model:** This model represents individual, distinct permissions (e.g., ``blog.add_post``, ``users.view_profile``). You can define as many specific permissions as your application needs for its regular user base.

* **``Group`` Model:** Groups act as roles for standard users. You can create groups (e.g., "Editors", "Moderators", "Managers") and assign a collection of ``UserPermission`` objects to each group. This simplifies permission management, as you assign users to groups rather than individually assigning many permissions to each user.

* **``User`` Model:** Users are then assigned to one or more ``Group`` objects. A user inherits all permissions from the groups they belong to. The ``User`` model includes a robust ``has_permission(permission_name: str) -> bool`` method which efficiently checks if a user possesses a specific permission, considering their group memberships.

**Key Features (Standard Users):**

* **Granular Control:** Define specific permissions that represent actions or access rights for standard users.
* **Efficient Checks:** The ``has_permission`` method on the ``User`` model uses caching to optimize performance, reducing database queries for frequently checked permissions.

---

2. Managing Permissions, Groups, and Users for Standard Users
-------------------------------------------------------------

The framework's **generic Admin Panel** provides a convenient interface for managing your standard user authorization structure:

* **Adding Permissions:** Through the Admin Panel, you can define new ``UserPermission`` entries, giving them a unique name and an optional description. These represent the individual capabilities in your system.
* **Creating Groups:** You can create new ``Group`` objects (roles) and assign a name and description.
* **Assigning Permissions to Groups:** Crucially, the Admin Panel allows you to easily associate any defined ``UserPermission`` with specific ``Group`` objects. For example, you could create an "Editor" group and assign it ``blog.add_post``, ``blog.edit_post``, and ``blog.delete_post`` permissions.
* **Assigning Users to Groups:** Finally, you can assign individual ``User`` accounts to one or more ``Group`` objects. A user will then inherit all permissions from the groups they are a member of.

This integrated approach means you don't have to write custom code for basic permission management; it's all handled through the Admin Panel.

---

3. Admin User Permissions and Hierarchy
---------------------------------------

The framework implements a distinct and robust permission system specifically for **administrative users**, operating separately from the standard user permission structure. This section details the permission hierarchy for admin users and how these permissions interact with the generic admin panel views.

#### Admin User Types and Their Privileges

The administrative users in your system are categorized into three distinct types, each with varying levels of access and control:

1.  **Supreme Admin (User ID 1): The Ultimate Authority**
    * **Identification:** This is typically the very first admin user created in the system, uniquely identified by having an ``id`` of ``1`` in the database.
    * **Permissions:** This user automatically possesses **all possible permissions** across the entire system. They bypass all explicit permission checks and can perform any action, including creating, modifying, and deleting any data or user, including other admin users (Super-admin and Regular Admin types). This user represents the absolute highest level of administrative control.

2.  **Super-admin (``is_superuser=True``): Elevated Administrative Control**
    * **Identification:** These admin users are designated by having their ``is_superuser`` flag explicitly set to ``True`` in their admin user profile.
    * **Permissions:** A ``Super-admin`` user inherently receives a broad set of elevated permissions across the system. They can manage their own data and, crucially, have the authority to **modify and delete data of Regular Admin users**. However, they **cannot** modify or delete the ``Supreme Admin`` (ID 1) or other ``Super-admin`` users, unless explicitly granted specific additional permissions via the Admin User Groups.
    * **Control:** They are typically responsible for managing the daily administrative operations and overseeing Regular Administrators.

3.  **Regular Admin:** Standard Administrative Access
    * **Identification:** These are administrative users whose ``is_superuser`` flag is ``False``. Their administrative access is governed by the specific permissions assigned to them through their associated **Admin User Groups**.
    * **Permissions:** Their access is strictly limited to the permissions explicitly granted to them. For example, a Regular Admin might have ``add_product`` and ``view_product`` permissions but lack ``delete_product``.
    * **Control:** They can only manage the data and sections for which they have explicit permissions. They **cannot** modify or delete other admin users (neither ``Supreme Admin``, ``Super-admin``, nor other ``Regular Admins``) unless specific administrative management permissions are assigned to their Admin User Groups (which is generally restricted to higher-tier admins).

---

#### Generic Admin Panel Permissions Enforcement (``@PermissionRequired``)

The framework's generic admin panel views are protected by the ``@PermissionRequired`` decorator. This decorator dynamically checks if the authenticated **admin user** has the necessary permission to access a specific view or perform an action on a model.

The permissions required for these generic views are dynamically constructed based on the action and the ``model_name`` being accessed. Here, ``model_name`` refers to the lowercase name of the database model (e.g., ``user``, ``product``, ``category``) that the view is interacting with.

* **Admin Dashboard Access:**
    * **Permission Required:** ``@PermissionRequired("view_dashboard")``
    * **Description:** Grants access to the main administrative dashboard.

* **Add Object View:**
    * **Permission Required:** ``@PermissionRequired(lambda request: f"add_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "add_unknown_model")``
    * **Example:** To add a new ``Product`` via the admin panel, the admin user needs the ``add_product`` permission.
    * **Description:** Allows access to the form for creating a new instance of a specified model.

* **Change Object View:**
    * **Permission Required:** ``@PermissionRequired(lambda request: f"change_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "change_unknown_model")``
    * **Example:** To edit an existing ``User`` through the admin panel, the admin user needs the ``change_user`` permission.
    * **Description:** Allows access to the form for modifying an existing instance of a specified model.

* **List Objects View:**
    * **Permission Required:** ``@PermissionRequired(lambda request: f"view_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "view_unknown_model")``
    * **Example:** To view the list of ``Products`` in the admin panel, the admin user needs the ``view_product`` permission.
    * **Description:** Allows admin users to view a list of all instances for a specified model.

* **Detail Object View:**
    * **Permission Required:** ``@PermissionRequired(lambda request: f"view_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "view_unknown_model")``
    * **Example:** To view the detailed information of a single ``User`` in the admin panel, the admin user needs the ``view_user`` permission.
    * **Description:** Allows admin users to view the detailed information of a single instance of a specified model.

* **Delete Object View:**
    * **Permission Required:** ``@PermissionRequired(lambda request: f"delete_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "delete_unknown_model")``
    * **Example:** To delete a ``Category`` via the admin panel, the admin user needs the ``delete_category`` permission.
    * **Description:** Allows admin users to delete an instance of a specified model.

**Important Note on Dynamic Permissions:** The ``lambda`` function within ``@PermissionRequired`` dynamically constructs the required permission string based on the ``model_name`` extracted from the URL path parameters. This ensures that permissions are granular and model-specific. If ``model_name`` is not found, a default "unknown_model" permission is used, which typically denies access.

---

#### Admin Panel Group and Role Management for Admin Users

Admin user permissions are managed within the framework's **Admin Panel** itself under the **Authentication & Authorization** section. This is where you configure the specific administrative roles and their corresponding permissions.

* **Create and Manage Admin User Groups:** Define new groups specifically for administrative roles (e.g., ``Content_Administrators``, ``Product_Supervisors``, ``System_Auditors``).
* **Assign Permissions to Admin Groups:** Crucially, select specific administrative permissions (e.g., ``admin.add_user_permission``, ``app_name.change_order``, ``app_name.delete_product``) and assign them to the relevant Admin User Groups.
* **Assign Admin Users to Admin Groups:** Finally, assign individual Admin User accounts to one or more Admin User Groups. An admin user will then inherit all permissions from the admin groups they are a member of.
* **Manage ``is_superuser`` Flag:** For ``Super-admin`` users, ensure their ``is_superuser`` flag is explicitly set to ``True`` in their individual admin user profile within the Admin Panel.

By carefully configuring Admin User Groups and assigning the appropriate permissions, you can precisely control access levels for all your administrative users, ensuring secure and efficient management of your application.

---

4. Enforcing Authorization with ``PermissionRequired`` Decorator (General Usage)
----------------------------------------------------------------------------

The primary way to enforce authorization on your views, for both standard users and admin users, is by using the ``PermissionRequired`` **decorator**. This decorator ensures that only users (of any type) with the necessary permissions can access a particular view.

How to Use:
-----------

You can apply the ``PermissionRequired`` decorator to your view functions or methods. It accepts one or more permission strings:

* **Single Permission:**

    .. code-block:: python

        # myapp/views.py
        from lback.auth.permissions import PermissionRequired
        from lback.utils.shortcuts import render
        
        @PermissionRequired("blog.view_posts")
        def view_blog_posts(request):
            # This view requires the 'blog.view_posts' permission
            # ... fetch blog posts ...
            return render(request, "blog/list.html", {"posts": posts})

* **Multiple Permissions (User needs ALL of them):**

    .. code-block:: python

        # myapp/views.py
        from lback.auth.permissions import PermissionRequired
        from lback.utils.shortcuts import render

        @PermissionRequired(["blog.add_post", "blog.publish_post"])
        def create_and_publish_post(request):
            # This view requires BOTH 'blog.add_post' AND 'blog.publish_post' permissions
            # ... logic to create and publish a post ...
            return render(request, "blog/new_post_success.html")

* **Dynamic Permissions (Permissions based on request context):**
    For more complex scenarios, you can provide a callable (a function) to ``PermissionRequired``. This function will receive the ``request`` object and should return the required permission(s) dynamically.

    .. code-block:: python

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

---

5. Permission Check Flow & Denied Access Handling
--------------------------------------------------

When a view decorated with ``PermissionRequired`` is accessed:

1.  The framework attempts to retrieve the authenticated ``user`` object from the ``request``.
2.  If the user is a **Supreme Admin** (User ID 1) or a **Super-admin** (``is_superuser=True``), access is immediately granted.
3.  Otherwise, the system calls the ``user.has_permission()`` method for each required permission.
4.  If the user lacks any of the specified permissions, access is denied.
5.  **Denied Access Handling:**
    * If the user is **not authenticated** at all, they are redirected to the login page (``/auth/login/``) with a flash message.
    * If the user is authenticated but **lacks the required permissions**, they are redirected to a 403 Forbidden page (``return_403``) with a flash message indicating denied access.

---

6. Signals for Authorization Flow
---------------------------------

The authorization process also dispatches signals, allowing you to hook into the permission checking lifecycle for custom logic or logging:

* ``permission_check_started``: Broadcast when a permission check begins.
    * **Sender:** ``PermissionRequired`` instance
    * **Kwargs:** ``request``, ``required_permissions`` (set of permissions being checked), ``user`` (the user object), ``view_func_name`` (name of the view function).
* ``permission_check_succeeded``: Broadcast when a user successfully passes a permission check.
    * **Sender:** ``PermissionRequired`` instance
    * **Kwargs:** ``request``, ``required_permissions``, ``user``, ``view_func_name``.
* ``permission_check_failed``: Broadcast when a user fails a permission check.
    * **Sender:** ``PermissionRequired`` instance
    * **Kwargs:** ``request``, ``required_permissions``, ``user``, ``view_func_name``, ``reason`` (e.g., "user_not_authenticated", "permission_missing").