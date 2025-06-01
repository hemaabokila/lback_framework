.. _admin-user-repository-signals:

Signals from AdminUserRepository
================================

The :py:class:`lback.repositories.admin_user_repository.AdminUserRepository` handles direct database interactions for :py:class:`~lback.models.adminuser.AdminUser` entities. This repository emits signals at critical stages of the create, update, and delete operations, providing **essential hooks for auditing changes to admin user data, triggering related business logic, or integrating with external data synchronization services.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``admin_user_pre_create``
     - Emitted just before a new `AdminUser` instance is created and added to the database session.
     - ``sender`` (:py:class:`~lback.repositories.admin_user_repository.AdminUserRepository`): The repository instance.<br>``data`` (:py:class:`dict`): The dictionary of data used to create the `AdminUser` (password is masked).<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``admin_user_post_create``
     - Emitted immediately after a new `AdminUser` instance has been successfully created and added to the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.admin_user_repository.AdminUserRepository`): The repository instance.<br>``admin_user`` (:py:class:`~lback.models.adminuser.AdminUser`): The newly created `AdminUser` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``admin_user_pre_update``
     - Emitted just before an existing `AdminUser` instance is updated with new data in the database session.
     - ``sender`` (:py:class:`~lback.repositories.admin_user_repository.AdminUserRepository`): The repository instance.<br>``admin_user`` (:py:class:`~lback.models.adminuser.AdminUser`): The `AdminUser` instance about to be updated.<br>``update_data`` (:py:class:`dict`): The dictionary of data used for the update (password is masked).<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``admin_user_post_update``
     - Emitted immediately after an existing `AdminUser` instance has been successfully updated in the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.admin_user_repository.AdminUserRepository`): The repository instance.<br>``admin_user`` (:py:class:`~lback.models.adminuser.AdminUser`): The updated `AdminUser` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``admin_user_pre_delete``
     - Emitted just before an `AdminUser` instance is marked for deletion in the database session.
     - ``sender`` (:py:class:`~lback.repositories.admin_user_repository.AdminUserRepository`): The repository instance.<br>``admin_user`` (:py:class:`~lback.models.adminuser.AdminUser`): The `AdminUser` instance about to be deleted.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``admin_user_post_delete``
     - Emitted immediately after an `AdminUser` instance has been successfully marked for deletion in the database session (but not yet committed).
     - ``sender`` (:py:class:`~lback.repositories.admin_user_repository.AdminUserRepository`): The repository instance.<br>``admin_user_id`` (:py:class:`int` or :py:class:`str`): The ID of the `AdminUser` that was marked for deletion.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.