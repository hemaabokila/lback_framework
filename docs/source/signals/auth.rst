.. _admin-auth-signals:

Signals from AdminAuth
======================

The :py:class:`lback.auth.admin_auth.AdminAuth` class, which specifically handles authentication and authorization for admin users, emits signals at various critical points throughout its operations. These signals are incredibly useful for **auditing admin actions, integrating with logging or monitoring systems, or implementing custom security logic** related to admin user management.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``admin_auth_initialized``
     - Emitted immediately after the :py:class:`AdminAuth` instance has been successfully initialized with its required managers.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The specific instance of the AdminAuth handler.
   * - ``admin_registration_attempt``
     - Emitted just before an attempt is made to register a new admin user.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``username`` (:py:class:`str`): The username provided for the registration attempt.<br>``email`` (:py:class:`str`): The email provided for the registration attempt.
   * - ``admin_registration_successful``
     - Emitted when a new admin user has been successfully registered (i.e., added to the database).
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``admin_user`` (:py:class:`Any`): The newly created admin user object.<br>``username`` (:py:class:`str`): The username of the registered admin.<br>``email`` (:py:class:`str`): The email of the registered admin.<br>``db_session`` (:py:class:`~sqlalchemy.orm.Session`): The SQLAlchemy database session used for the operation.
   * - ``admin_registration_failed``
     - Emitted when an attempt to register an admin user fails.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``username`` (:py:class:`str`): The username for the failed registration attempt.<br>``email`` (:py:class:`str`): The email for the failed registration attempt.<br>``error_type`` (:py:class:`str`): A string indicating the type of failure (e.g., "manager_returned_none").<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an unexpected error.
   * - ``admin_login_attempt``
     - Emitted just before an attempt is made to log in an admin user.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``username`` (:py:class:`str`): The username provided for the login attempt.<br>``request`` (:py:class:`~lback.http.request.Request`): The incoming request object.
   * - ``admin_login_successful``
     - Emitted when an admin user has successfully authenticated and their session has been initiated.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``admin_user`` (:py:class:`Any`): The authenticated admin user object.<br>``username`` (:py:class:`str`): The username of the logged-in admin.<br>``request`` (:py:class:`~lback.http.request.Request`): The incoming request object.
   * - ``admin_login_failed``
     - Emitted when an attempt to log in an admin user fails (e.g., due to invalid credentials or an internal error).
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``username`` (:py:class:`str`): The username for the failed login attempt.<br>``request`` (:py:class:`~lback.http.request.Request`): The incoming request object.<br>``reason`` (:py:class:`str`): A string describing the reason for the failure (e.g., "authentication_failed", "exception").<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an unexpected error.
   * - ``admin_logout_attempt``
     - Emitted just before an admin user's session is terminated as part of a logout process.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``user_session`` (:py:class:`~lback.session.AppSession` or :py:class:`None`): The session object associated with the user, if available.<br>``session_id`` (:py:class:`str`): The ID of the session being logged out (or 'N/A' if not found).<br>``user_id`` (:py:class:`str` or :py:class:`None`): The ID of the user associated with the session, if found.
   * - ``admin_logout_successful``
     - Emitted when an admin user's session has been successfully ended (deleted).
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``session_id`` (:py:class:`str`): The ID of the session that was successfully logged out.<br>``user_id`` (:py:class:`str` or :py:class:`None`): The ID of the user whose session was logged out.
   * - ``admin_authentication_check``
     - Emitted after an attempt to verify if an admin user is currently logged in via their session.
     - ``sender`` (:py:class:`~lback.auth.admin_auth.AdminAuth`): The AdminAuth instance.<br>``request`` (:py:class:`~lback.http.request.Request`): The incoming request object.<br>``is_admin`` (:py:class:`bool`): ``True`` if an admin user is currently logged in, ``False`` otherwise.<br>``reason`` (:py:class:`str`): A string explaining the outcome of the check (e.g., "authenticated_session_is_admin", "session_authentication_failed").

.. _jwt-auth-signals:

Signals from JWTAuth
====================

The :py:class:`lback.auth.jwt_auth.JWTAuth` class, which provides utilities for creating, decoding, and validating JSON Web Tokens (JWTs), emits signals at various stages of token lifecycle and validation. These signals are highly valuable for **auditing token issuance, monitoring authentication attempts, and integrating with security logging systems.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``jwt_access_token_created``
     - Emitted when a new access token has been successfully created.
     - ``sender`` (:py:class:`~lback.auth.jwt_auth.JWTAuth`): The JWTAuth instance.<br>``payload`` (:py:class:`dict`): The payload dictionary encoded into the token.<br>``token`` (:py:class:`str`): The full encoded JWT access token string.
   * - ``jwt_refresh_token_created``
     - Emitted when a new refresh token has been successfully created.
     - ``sender`` (:py:class:`~lback.auth.jwt_auth.JWTAuth`): The JWTAuth instance.<br>``payload`` (:py:class:`dict`): The payload dictionary encoded into the token.<br>``token`` (:py:class:`str`): The full encoded JWT refresh token string.
   * - ``jwt_token_decoded``
     - Emitted when a JWT token has been successfully decoded and its signature and expiration verified.
     - ``sender`` (:py:class:`~lback.auth.jwt_auth.JWTAuth`): The JWTAuth instance.<br>``token`` (:py:class:`str`): The original JWT token string.<br>``payload`` (:py:class:`dict`): The decoded payload dictionary of the token.
   * - ``jwt_decode_failed``
     - Emitted when a JWT token fails to decode or validate due to various reasons (e.g., expired, invalid signature, malformed).
     - ``sender`` (:py:class:`~lback.auth.jwt_auth.JWTAuth`): The JWTAuth instance.<br>``token`` (:py:class:`str`): The JWT token string that failed to decode/validate.<br>``error_type`` (:py:class:`str`): A string indicating the specific reason for failure (e.g., "empty_token", "expired", "invalid_signature", "invalid_audience", "invalid_issuer", "invalid_issued_at", "decode_error", "unexpected_exception", "type_mismatch").<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an unexpected error.<br>``expected_type`` (:py:class:`str`, *optional*): The expected token type, if a type mismatch occurred.<br>``actual_type`` (:py:class:`str`, *optional*): The actual token type found in the payload, if a type mismatch occurred.

.. _oauth2-auth-signals:

Signals from OAuth2Auth
=======================

The :py:class:`lback.auth.oauth2_auth.OAuth2Auth` class is a crucial utility for handling interactions with an OAuth2 provider, specifically implementing the Authorization Code Grant flow. This class emits signals at key stages of the OAuth2 process, providing **invaluable insights for monitoring authentication flows, debugging integrations, and auditing user consent and token management.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``oauth2_authorize_url_generated``
     - Emitted right after the full authorization URL has been constructed and is ready to be used for redirecting the user to the OAuth2 provider.
     - ``sender`` (:py:class:`~lback.auth.oauth2_auth.OAuth2Auth`): The OAuth2Auth instance.<br>``authorize_url`` (:py:class:`str`): The complete URL generated for authorization.<br>``state`` (:py:class:`str` or :py:class:`None`): The `state` parameter included in the URL, if provided.<br>``scope`` (:py:class:`str`): The requested `scope` for the authorization.
   * - ``oauth2_token_fetched``
     - Emitted when an authorization code has been successfully exchanged for an access token (and potentially a refresh token) from the OAuth2 provider.
     - ``sender`` (:py:class:`~lback.auth.oauth2_auth.OAuth2Auth`): The OAuth2Auth instance.<br>``code`` (:py:class:`str`): The authorization code that was exchanged.<br>``token_data`` (:py:class:`dict`): The dictionary response from the OAuth2 provider's token endpoint (e.g., containing `access_token`, `token_type`, `expires_in`, `refresh_token`).
   * - ``oauth2_token_fetch_failed``
     - Emitted when the attempt to exchange an authorization code for a token fails due to network issues, invalid code, or provider errors.
     - ``sender`` (:py:class:`~lback.auth.oauth2_auth.OAuth2Auth`): The OAuth2Auth instance.<br>``code`` (:py:class:`str`): The authorization code that was used in the failed attempt.<br>``error`` (:py:class:`str`): A descriptive string indicating the reason for the failure (e.g., "timeout", "http_error_400", "request_error", "unexpected_exception").
   * - ``oauth2_token_refreshed``
     - Emitted when a refresh token has been successfully used to obtain a new access token (and optionally a new refresh token).
     - ``sender`` (:py:class:`~lback.auth.oauth2_auth.OAuth2Auth`): The OAuth2Auth instance.<br>``old_refresh_token`` (:py:class:`str`): The refresh token that was used for the refresh operation.<br>``new_token_data`` (:py:class:`dict`): The dictionary response from the OAuth2 provider's token endpoint, containing the newly issued tokens.
   * - ``oauth2_token_refresh_failed``
     - Emitted when the attempt to refresh a token fails, possibly due to an expired or invalid refresh token, or provider errors.
     - ``sender`` (:py:class:`~lback.auth.oauth2_auth.OAuth2Auth`): The OAuth2Auth instance.<br>``old_refresh_token`` (:py:class:`str`): The refresh token that was used in the failed attempt.<br>``error`` (:py:class:`str`): A descriptive string indicating the reason for the failure (e.g., "timeout", "http_error_400", "request_error", "unexpected_exception").

.. _permission-required-signals:

Signals from PermissionRequired
===============================

The :py:class:`lback.auth.decorators.PermissionRequired` decorator plays a crucial role in securing views by enforcing granular permission checks. This class emits signals at key stages of the permission evaluation process, offering **valuable hooks for auditing access attempts, integrating with security logging systems, or implementing custom response logic based on access outcomes.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``permission_check_started``
     - Emitted at the very beginning of the permission check process for a decorated view.
     - ``sender`` (:py:class:`~lback.auth.decorators.PermissionRequired`): The decorator instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``required_permissions`` (:py:class:`set` of :py:class:`str`): The set of permissions being checked.<br>``user`` (:py:class:`Any` or :py:class:`None`): The user object associated with the request (can be `None` if not authenticated).<br>``view_func_name`` (:py:class:`str`): The name of the view function being accessed.
   * - ``permission_check_succeeded``
     - Emitted when the authenticated user successfully passes all required permission checks for a view.
     - ``sender`` (:py:class:`~lback.auth.decorators.PermissionRequired`): The decorator instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``required_permissions`` (:py:class:`set` of :py:class:`str`): The set of permissions that were successfully met.<br>``user`` (:py:class:`Any` or :py:class:`None`): The user object that passed the check.<br>``view_func_name`` (:py:class:`str`): The name of the view function accessed.
   * - ``permission_check_failed``
     - Emitted when the authenticated user (or lack thereof) fails to meet the required permissions for a view.
     - ``sender`` (:py:class:`~lback.auth.decorators.PermissionRequired`): The decorator instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``required_permissions`` (:py:class:`set` of :py:class:`str`): The set of permissions that were required.<br>``user`` (:py:class:`Any` or :py:class:`None`): The user object that failed the check (can be `None`).<br>``view_func_name`` (:py:class:`str`): The name of the view function for which permission was denied.<br>``reason`` (:py:class:`str`): A string indicating the specific reason for the failure (e.g., "user_not_authenticated", "user_model_missing_has_permission_method", or specific missing permission).

.. _session-auth-signals:

Signals from SessionAuth
========================

The :py:class:`lback.auth.session_auth.SessionAuth` utility is central to managing user authentication via sessions. It provides a robust way to track user login states and session lifecycle. This class emits signals at critical points during user login, logout, and session status checks, enabling **detailed auditing, real-time monitoring of user activity, and integration with other security or logging mechanisms.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``user_logged_in``
     - Emitted when a user is successfully logged in and their `user_id` and `user_type` have been set in an active session.
     - ``sender`` (:py:class:`~lback.auth.session_auth.SessionAuth`): The SessionAuth instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``user_id`` (:py:class:`Union`[:py:class:`int`, :py:class:`str`, :py:class:`~uuid.UUID`]): The ID of the user who logged in.<br>``user_type`` (:py:class:`str`): The type of the user (e.g., "user", "admin").<br>``session`` (:py:class:`~lback.utils.app_session.AppSession`): The active `AppSession` instance used for login.
   * - ``session_login_failed``
     - Emitted when an attempt to log a user in via session fails (e.g., due to an unavailable or invalid session object on the request).
     - ``sender`` (:py:class:`~lback.auth.session_auth.SessionAuth`): The SessionAuth instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``user_id`` (:py:class:`Union`[:py:class:`int`, :py:class:`str`, :py:class:`~uuid.UUID`]): The ID of the user for whom login was attempted.<br>``user_type`` (:py:class:`str`): The type of the user for whom login was attempted.<br>``reason`` (:py:class:`str`): A string describing the reason for the failure (e.g., "session_unavailable", "invalid_session_object", "session_inactive", "session_expiry_missing").
   * - ``session_authentication_check``
     - Emitted after checking the authentication status of a user based on their session data.
     - ``sender`` (:py:class:`~lback.auth.session_auth.SessionAuth`): The SessionAuth instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``user_id`` (:py:class:`Union`[:py:class:`int`, :py:class:`str`, :py:class:`~uuid.UUID`] or :py:class:`None`): The ID of the user if found in the session, otherwise `None`.<br>``is_authenticated`` (:py:class:`bool`): ``True`` if the user is considered authenticated via session, ``False`` otherwise.<br>``reason`` (:py:class:`str`): A string explaining the outcome of the check (e.g., "authenticated_and_active", "active_but_no_user_id", "session_inactive", "session_expiry_missing", "session_unavailable").
   * - ``user_logged_out``
     - Emitted when a user's session is successfully deleted as part of the logout process.
     - ``sender`` (:py:class:`~lback.auth.session_auth.SessionAuth`): The SessionAuth instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``session_id`` (:py:class:`str`): The ID of the session that was deleted.<br>``user_id`` (:py:class:`Union`[:py:class:`int`, :py:class:`str`, :py:class:`~uuid.UUID`] or :py:class:`None`): The ID of the user who was logged out, if available from the session before deletion.