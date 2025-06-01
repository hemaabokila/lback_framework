.. _role-repository-signals:

Signals from RoleRepository
===========================

The :py:class:`lback.repositories.role_repository.RoleRepository` manages direct database interactions for :py:class:`~lback.models.adminuser.Role` entities. This repository emits signals at crucial stages of create, update, and delete operations, offering **essential hooks for auditing role changes, triggering custom business logic, or synchronizing role assignments across different application components.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``role_pre_create``
     - Emitted just before a new `Role` instance is created and added to the database session.
     - ``sender`` (:py:class:`~lback.repositories.role_repository.RoleRepository`): The repository instance.<br>``data`` (:py:class:`dict`): The dictionary of data used to create the `Role`.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``role_post_create``
     - Emitted immediately after a new `Role` instance has been successfully created and added to the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.role_repository.RoleRepository`): The repository instance.<br>``role`` (:py:class:`~lback.models.adminuser.Role`): The newly created `Role` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``role_pre_update``
     - Emitted just before an existing `Role` instance is updated with new data in the database session.
     - ``sender`` (:py:class:`~lback.repositories.role_repository.RoleRepository`): The repository instance.<br>``role`` (:py:class:`~lback.models.adminuser.Role`): The `Role` instance about to be updated.<br>``update_data`` (:py:class:`dict`): The dictionary of data used for the update.
     - ``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``role_post_update``
     - Emitted immediately after an existing `Role` instance has been successfully updated in the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.role_repository.RoleRepository`): The repository instance.<br>``role`` (:py:class:`~lback.models.adminuser.Role`): The updated `Role` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``role_pre_delete``
     - Emitted just before a `Role` instance is marked for deletion in the database session.
     - ``sender`` (:py:class:`~lback.repositories.role_repository.RoleRepository`): The repository instance.<br>``role`` (:py:class:`~lback.models.adminuser.Role`): The `Role` instance about to be deleted.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``role_post_delete``
     - Emitted immediately after a `Role` instance has been successfully marked for deletion in the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.role_repository.RoleRepository`): The repository instance.<br>``role_id`` (:py:class:`int` or :py:class:`str`): The ID of the `Role` that was marked for deletion.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.