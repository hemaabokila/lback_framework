.. _user-model-signals:

Signals from User Model
=======================

The :py:class:`lback.auth.models.User` model emits several signals during critical user-related operations, such as password management and email verification. These signals offer **valuable integration points for auditing user actions, triggering notifications, updating external systems, or implementing custom logic tied to user authentication and account management flows.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``user_password_set``
     - Emitted successfully after a user's password has been hashed and set on the user model.
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model whose password was set.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.
   * - ``user_password_set_failed``
     - Emitted if an error occurs during the process of hashing or setting a user's password.
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model on which the password set failed.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.<br>``exception`` (:py:class:`Exception`): The exception object that caused the failure.
   * - ``user_password_checked``
     - Emitted after a user's plain text password has been checked against the stored hashed password.
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model whose password was checked.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.<br>``success`` (:py:class:`bool`): `True` if the password matched, `False` otherwise.
   * - ``user_password_check_failed``
     - Emitted if an error occurs during the process of checking a user's password (e.g., due to an issue with the hashing library).
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model on which the password check failed.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.<br>``exception`` (:py:class:`Exception`): The exception object that caused the failure.
   * - ``user_email_verification_token_generated``
     - Emitted after a new email verification token has been successfully generated and assigned to the user.
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model for which the token was generated.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.
   * - ``user_email_verified``
     - Emitted when a user's email address has been successfully verified using a valid token.
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model whose email was verified.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.
   * - ``user_email_verification_failed``
     - Emitted when an attempt to verify a user's email address fails (e.g., due to an invalid or expired token).
     - ``sender`` (:py:class:`~lback.auth.models.User`): The instance of the `User` model for which email verification failed.<br>``user`` (:py:class:`~lback.auth.models.User`): The `User` object itself.