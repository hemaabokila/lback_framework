.. _user-repository-signals:

Signals from UserRepository
===========================

The :py:class:`lback.repositories.user_repository.UserRepository` handles all direct database interactions for :py:class:`~lback.models.user.User` entities. This repository is designed to emit **signals at crucial points in the user lifecycle** (create, update, delete). These signals are invaluable for various purposes, including:

* **Auditing**: Tracking changes to user accounts for security and compliance.
* **Notifications**: Triggering emails (e.g., welcome emails, account updates) or other alerts.
* **Integrations**: Synchronizing user data with external systems.
* **Custom Logic**: Implementing bespoke actions before or after user data modifications.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``user_pre_create``
     - Emitted just **before** a new `User` instance is created and added to the database session. This allows for validation or modification of data before persistence.
     - ``sender`` (:py:class:`~lback.repositories.user_repository.UserRepository`): The repository instance.<br>``data`` (:py:class:`dict`): The dictionary of data used to create the `User` (password is masked for security).<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``user_post_create``
     - Emitted immediately **after** a new `User` instance has been successfully created and added to the database session (but not yet committed). Useful for post-creation actions like sending welcome emails.
     - ``sender`` (:py:class:`~lback.repositories.user_repository.UserRepository`): The repository instance.<br>``user`` (:py:class:`~lback.models.user.User`): The newly created `User` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``user_pre_update``
     - Emitted just **before** an existing `User` instance is updated with new data in the database session. This is ideal for pre-update validation or preparing audit trails.
     - ``sender`` (:py:class:`~lback.repositories.user_repository.UserRepository`): The repository instance.<br>``user`` (:py:class:`~lback.models.user.User`): The `User` instance about to be updated.<br>``update_data`` (:py:class:`dict`): The dictionary of data used for the update (password is masked for security).<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``user_post_update``
     - Emitted immediately **after** an existing `User` instance has been successfully updated in the database session (but not yet committed). Useful for post-update notifications or cache invalidation.
     - ``sender`` (:py:class:`~lback.repositories.user_repository.UserRepository`): The repository instance.<br>``user`` (:py:class:`~lback.models.user.User`): The updated `User` instance.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``user_pre_delete``
     - Emitted just **before** a `User` instance is marked for deletion in the database session. This can be used for final checks or archiving data.
     - ``sender`` (:py:class:`~lback.repositories.user_repository.UserRepository`): The repository instance.<br>``user`` (:py:class:`~lback.models.user.User`): The `User` instance about to be deleted.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.
   * - ``user_post_delete``
     - Emitted immediately **after** a `User` instance has been successfully marked for deletion in the database session (but not yet committed). Useful for cleanup tasks or confirming deletion in external systems.
     - ``sender`` (:py:class:`~lback.repositories.user_repository.UserRepository`): The repository instance.<br>``user_id`` (:py:class:`int` or :py:class:`str`): The ID of the `User` that was marked for deletion.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session being used for the operation.