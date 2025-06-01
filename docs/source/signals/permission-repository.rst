.. _permission-repository-signals:

Signals from PermissionRepository
=================================

The :py:class:`lback.repositories.permission_repository.PermissionRepository` manages direct database interactions for :py:class:`~lback.models.adminuser.Permission` entities. This repository emits signals at crucial stages of create, update, and delete operations, offering **vital hooks for auditing permission changes, triggering custom validation rules, or synchronizing permission data across different application components.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``permission_pre_create``
     - Emitted just before a new `Permission` instance is created and added to the database session.
     - ``sender`` (:py:class:`~lback.repositories.permission_repository.PermissionRepository`): The repository instance.<br>``data`` (:py:class:`dict`): The dictionary of data used to create the `Permission`.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``permission_post_create``
     - Emitted immediately after a new `Permission` instance has been successfully created and added to the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.permission_repository.PermissionRepository`): The repository instance.<br>``permission`` (:py:class:`~lback.models.adminuser.Permission`): The newly created `Permission` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``permission_pre_update``
     - Emitted just before an existing `Permission` instance is updated with new data in the database session.
     - ``sender`` (:py:class:`~lback.repositories.permission_repository.PermissionRepository`): The repository instance.<br>``permission`` (:py:class:`~lback.models.adminuser.Permission`): The `Permission` instance about to be updated.<br>``update_data`` (:py:class:`dict`): The dictionary of data used for the update.
     - ``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``permission_post_update``
     - Emitted immediately after an existing `Permission` instance has been successfully updated in the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.permission_repository.PermissionRepository`): The repository instance.<br>``permission`` (:py:class:`~lback.models.adminuser.Permission`): The updated `Permission` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``permission_pre_delete``
     - Emitted just before a `Permission` instance is marked for deletion in the database session.
     - ``sender`` (:py:class:`~lback.repositories.permission_repository.PermissionRepository`): The repository instance.<br>``permission`` (:py:class:`~lback.models.adminuser.Permission`): The `Permission` instance about to be deleted.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``permission_post_delete``
     - Emitted immediately after a `Permission` instance has been successfully marked for deletion in the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.permission_repository.PermissionRepository`): The repository instance.<br>``permission_id`` (:py:class:`int` or :py:class:`str`): The ID of the `Permission` that was marked for deletion.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.