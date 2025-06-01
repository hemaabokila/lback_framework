.. _admin-user-manager-signals:

Signals from AdminUserManager
=============================

The :py:class:`lback.managers.admin_user_manager.AdminUserManager` is a crucial service layer responsible for orchestrating **admin user-related business logic**, such as registration and authentication. This manager strategically emits signals at various stages of these sensitive workflows. These signals are exceptionally valuable for:

* **Auditing and Logging**: Providing a detailed trail of administrative activities, especially for security-sensitive operations like new user creation or authentication attempts.
* **Integrations**: Hooking into external systems for tasks like sending welcome emails, syncing user data to a CRM, or notifying security teams of failed login attempts.
* **Custom Business Logic**: Implementing bespoke logic or side effects that need to occur at specific points in the admin user lifecycle without tightly coupling them to the core manager logic.
* **Monitoring and Alerting**: Setting up alerts for critical events like registration failures or suspicious authentication patterns.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``admin_registration_started``
     - Emitted at the very beginning of the ``register_admin`` process, before any validation or database interaction.
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username provided for registration.<br>``email`` (:py:class:`str`): The email provided for registration.<br>``role_name`` (:py:class:`Optional[str]`): The optional role name provided.
   * - ``admin_pre_register``
     - Emitted just before the admin user is created in the repository, after initial validation and password hashing.
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username being registered.<br>``email`` (:py:class:`str`): The email being registered.<br>``role_name`` (:py:class:`Optional[str]`): The role name assigned, if any.
   * - ``admin_registered``
     - Emitted after an admin user has been successfully created by the repository (but before the session is committed).
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``admin_user`` (:py:class:`~lback.models.adminuser.AdminUser`): The newly created AdminUser object.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``admin_registration_failed``
     - Emitted when the admin user registration process encounters any error (e.g., validation, password hashing, database issues, role not found).
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username attempted for registration.<br>``email`` (:py:class:`str`): The email attempted for registration.<br>``role_name`` (:py:class:`Optional[str]`): The optional role name provided.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "validation_error", "password_hashing_error", "role_not_found", "unexpected_exception").<br>``error_message`` (:py:class:`Optional[str]`): A human-readable error message (present for validation errors).<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.
   * - ``admin_authentication_started``
     - Emitted at the very beginning of the ``authenticate_admin`` process, before attempting to retrieve the user or verify credentials.
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username provided for authentication.
   * - ``admin_authenticated``
     - Emitted when an admin user has successfully authenticated.
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``admin_user`` (:py:class:`~lback.models.adminuser.AdminUser`): The authenticated AdminUser object.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``admin_authentication_failed``
     - Emitted when an admin user fails to authenticate for any reason (e.g., user not found, incorrect password, inactive user).
     - ``sender`` (:py:class:`~lback.managers.admin_user_manager.AdminUserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username attempted for authentication.<br>``reason`` (:py:class:`str`): A string indicating the reason for failure (e.g., "user_not_found", "incorrect_password", "user_inactive", "unexpected_exception").<br>``admin_user`` (:py:class:`Optional[~lback.models.adminuser.AdminUser]`): The AdminUser object if found, even if authentication failed (e.g., inactive user).<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.