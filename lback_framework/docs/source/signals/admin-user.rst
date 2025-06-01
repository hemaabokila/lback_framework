.. _admin-user-role-signals:

Signals from AdminUser and Role Models
======================================

The :py:class:`lback.admin.models.AdminUser` and :py:class:`lback.admin.models.Role` models emit signals during key operations related to administrative user permissions and role management. These signals provide **critical hooks for auditing administrative actions, implementing fine-grained logging, and integrating with external systems for security monitoring or compliance purposes.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``admin_user_permission_checked``
     - Emitted after checking whether an `AdminUser` has a specific permission. This signal provides insight into permission evaluation outcomes.
     - ``sender`` (:py:class:`~lback.admin.models.AdminUser`): The instance of the `AdminUser` model.<br>``admin_user`` (:py:class:`~lback.admin.models.AdminUser`): The `AdminUser` object whose permission was checked.<br>``permission_name`` (:py:class:`str`): The name of the permission that was checked.<br>``has_permission`` (:py:class:`bool`): `True` if the user has the permission, `False` otherwise.<br>``reason`` (:py:class:`str`): A string indicating why the permission was granted or denied (e.g., "is_superuser", "found_in_role_permissions", "not_found_in_role_permissions", "no_role_or_permissions").
   * - ``role_permission_added``
     - Emitted successfully after a new :py:class:`~lback.admin.models.Permission` has been added to a :py:class:`~lback.admin.models.Role`.
     - ``sender`` (:py:class:`~lback.admin.models.Role`): The instance of the `Role` model to which the permission was added.<br>``role`` (:py:class:`~lback.admin.models.Role`): The `Role` object itself.<br>``permission`` (:py:class:`~lback.admin.models.Permission`): The `Permission` object that was added.
   * - ``role_permission_removed``
     - Emitted successfully after a :py:class:`~lback.admin.models.Permission` has been removed from a :py:class:`~lback.admin.models.Role`.
     - ``sender`` (:py:class:`~lback.admin.models.Role`): The instance of the `Role` model from which the permission was removed.<br>``role`` (:py:class:`~lback.admin.models.Role`): The `Role` object itself.<br>``permission`` (:py:class:`~lback.admin.models.Permission`): The `Permission` object that was removed.
   * - ``role_permission_operation_failed``
     - Emitted if an attempt to add or remove a permission from a role fails (e.g., due to invalid type, permission already existing, or permission not found).
     - ``sender`` (:py:class:`~lback.admin.models.Role`): The instance of the `Role` model on which the operation failed.<br>``role`` (:py:class:`~lback.admin.models.Role`): The `Role` object itself.<br>``operation`` (:py:class:`str`): The attempted operation ("add" or "remove").<br>``permission`` (:py:class:`~lback.admin.models.Permission`): The `Permission` object involved in the failed operation (can be of any type if `invalid_type`).<br>``error_type`` (:py:class:`str`): Describes the type of failure (e.g., "invalid_type", "already_exists", "not_found").