.. _user-manager-signals:

Signals from UserManager
========================

The :py:class:`lback.managers.user_manager.UserManager` acts as the service layer for core user-related business logic, including registration, authentication, and password management. This manager strategically emits signals at various critical points within these workflows, providing **invaluable integration points for auditing, triggering notifications, synchronizing with external systems, and implementing custom business logic** without tightly coupling it to the core user management processes.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``user_registration_started``
     - Emitted at the very beginning of the ``register_user`` process, before any validation or database interaction.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username provided for registration.<br>``email`` (:py:class:`str`): The email provided for registration.
   * - ``user_pre_register``
     - Emitted just before the user is created in the repository, after initial validation and password hashing.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username being registered.<br>``email`` (:py:class:`str`): The email being registered.
   * - ``user_registered``
     - Emitted after a user has been successfully created by the repository and assigned to the default group (but before the session is committed), and email verification has been initiated.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user`` (:py:class:`~lback.models.user.User`): The newly created `User` object.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``user_email_verification_initiated``
     - Emitted after a user's email verification token has been generated and the verification email has been successfully sent.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user`` (:py:class:`~lback.models.user.User`): The `User` object for whom verification was initiated.
   * - ``user_registration_failed``
     - Emitted when the user registration process encounters any error (e.g., validation, password hashing, database issues, email sending failure).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username attempted for registration.<br>``email`` (:py:class:`str`): The email attempted for registration.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "validation_error", "email_send_failed", "repository_error", "unexpected_exception").<br>``error_message`` (:py:class:`Optional[str]`): A human-readable error message (present for validation errors).<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.
   * - ``user_authentication_started``
     - Emitted at the very beginning of the ``authenticate_user`` process, before attempting to retrieve the user or verify credentials.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username provided for authentication.
   * - ``user_authenticated``
     - Emitted when a user has successfully authenticated.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user`` (:py:class:`~lback.models.user.User`): The authenticated `User` object.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``user_authentication_failed``
     - Emitted when a user fails to authenticate for any reason (e.g., user not found, incorrect password, inactive user, unverified email).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``username`` (:py:class:`str`): The username attempted for authentication.<br>``reason`` (:py:class:`str`): A string indicating the reason for failure (e.g., "user_not_found", "incorrect_password", "user_inactive", "email_not_verified", "unexpected_exception").<br>``user`` (:py:class:`Optional[~lback.models.user.User]`): The `User` object if found, even if authentication failed (e.g., inactive user).<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.
   * - ``user_email_verification_successful``
     - Emitted when a user's email address has been successfully verified.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user`` (:py:class:`~lback.models.user.User`): The `User` object whose email was successfully verified.<br>``reason`` (:py:class:`Optional[str]`): An optional reason for success (e.g., "already_verified" if the email was already verified).
   * - ``user_email_verification_failed``
     - Emitted when an attempt to verify a user's email address fails (e.g., invalid token, expired token, or other errors).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``token_prefix`` (:py:class:`str`): The first 10 characters of the token used for verification.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "invalid_token", "token_mismatch_or_expired", "unexpected_exception").<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.<br>``user`` (:py:class:`Optional[~lback.models.user.User]`): The `User` object if found, even if verification failed.
   * - ``user_update_started``
     - Emitted at the beginning of the ``update_user`` process, before retrieving the user or applying updates.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user_id`` (:py:class:`int`): The ID of the user being updated.<br>``update_data`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The data provided for the update.
   * - ``user_updated``
     - Emitted after a user's data has been successfully updated by the repository (but before the session is committed).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user`` (:py:class:`~lback.models.user.User`): The updated `User` object.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``user_update_failed``
     - Emitted when the user update process encounters any error (e.g., user not found, validation, password hashing, repository error).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user_id`` (:py:class:`int`): The ID of the user attempted for update.<br>``update_data`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The data attempted for update.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "user_not_found", "password_hashing_error", "repository_error", "unexpected_exception").<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.<br>``user`` (:py:class:`Optional[~lback.models.user.User]`): The `User` object if found.
   * - ``user_deletion_started``
     - Emitted at the beginning of the ``delete_user`` process, before retrieving the user or initiating deletion.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user_id`` (:py:class:`int`): The ID of the user being deleted.
   * - ``user_deleted``
     - Emitted after a user has been successfully marked for deletion by the repository (but before the session is committed).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user_id`` (:py:class:`int`): The ID of the user that was deleted.<br>``username`` (:py:class:`str`): The username of the deleted user.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``user_deletion_failed``
     - Emitted when the user deletion process encounters any error (e.g., user not found, repository error).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user_id`` (:py:class:`int`): The ID of the user attempted for deletion.<br>``username`` (:py:class:`Optional[str]`): The username of the user if available.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "user_not_found", "repository_error", "unexpected_exception").<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.
   * - ``password_reset_request_started``
     - Emitted at the beginning of the ``reset_password_request`` process, before retrieving the user or generating a token.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``email`` (:py:class:`str`): The email address for which the reset was requested.
   * - ``password_reset_request_processed``
     - Emitted after a password reset token has been generated, assigned to the user, and the reset email has been successfully sent.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``email`` (:py:class:`str`): The email address for which the reset was requested.<br>``user`` (:py:class:`~lback.models.user.User`): The `User` object for whom the reset was processed.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``password_reset_request_failed``
     - Emitted when a password reset request fails for any reason (e.g., user not found, email sending failure).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``email`` (:py:class:`str`): The email address for which the reset was requested.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "user_not_found", "email_send_failed", "unexpected_exception").<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.
   * - ``password_reset_started``
     - Emitted at the beginning of the ``reset_password`` process, before validating the token or updating the password.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``token_prefix`` (:py:class:`str`): The first 10 characters of the reset token.
   * - ``password_reset_successful``
     - Emitted after a user's password has been successfully reset using a valid token.
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``user`` (:py:class:`~lback.models.user.User`): The `User` object whose password was reset.<br>``session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy session used for the operation.
   * - ``password_reset_failed``
     - Emitted when a password reset attempt fails (e.g., invalid token, expired token, invalid new password, or other errors).
     - ``sender`` (:py:class:`~lback.managers.user_manager.UserManager`): The manager instance.<br>``token_prefix`` (:py:class:`str`): The first 10 characters of the reset token.<br>``error_type`` (:py:class:`str`): A string indicating the type of error (e.g., "invalid_token", "validation_error", "repository_error", "unexpected_exception").<br>``exception`` (:py:class:`Optional[Exception]`): The exception object if an unexpected exception occurred.<br>``user`` (:py:class:`Optional[~lback.models.user.User]`): The `User` object if found, even if reset failed.