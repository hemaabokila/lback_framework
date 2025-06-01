.. _session-manager-signals:

Signals from SessionManager
===========================

The :py:class:`lback.utils.session_manager.SessionManager` class, which handles server-side user sessions, emits signals at crucial points throughout the session lifecycle. These signals are incredibly useful for **logging, auditing, and integrating custom logic** related to how sessions are created, renewed, and deleted.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``session_manager_initialized``
     - Emitted right after the :py:class:`SessionManager` instance has been set up and is ready for use.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The instance of the session manager.<br>``timeout`` (:py:class:`~datetime.timedelta`): The configured duration for session expiration.
   * - ``session_created``
     - Emitted when a brand new session record is successfully added to the database.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The unique identifier of the newly created session.<br>``user_id`` (:py:class:`str` or :py:class:`None`): The ID of the user linked to this session, if any.
   * - ``session_creation_failed``
     - Emitted if an error prevents the successful creation of a new session.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``user_id`` (:py:class:`str` or :py:class:`None`): The user ID for whom the session creation was attempted.<br>``exception`` (:py:class:`Exception`): The actual exception object that caused the failure.
   * - ``session_renewed``
     - Emitted when an existing session's expiration timestamp is successfully extended. This often happens automatically on active requests.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session that was renewed.<br>``expires_at`` (:py:class:`~datetime.datetime`): The new expiration timestamp.
   * - ``session_renewal_failed``
     - Emitted when an attempt to renew a session fails (e.g., the session couldn't be found in the database).
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session that failed to renew.<br>``reason`` (:py:class:`str`): A short string explaining the failure (e.g., "not_found").
   * - ``session_deleted``
     - Emitted when a session record is successfully removed from the database.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session that was removed.
   * - ``session_deletion_failed``
     - Emitted when an attempt to delete a session is unsuccessful (e.g., the session wasn't found).
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session that failed to delete.<br>``reason`` (:py:class:`str`): A short string explaining the failure (e.g., "not_found").
   * - ``session_data_retrieved``
     - Emitted when session-specific data is successfully fetched from the database.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session whose data was retrieved.<br>``data_keys`` (:py:class:`list` of :py:class:`str`): A list of the top-level keys found within the retrieved session data dictionary.
   * - ``session_data_retrieval_failed``
     - Emitted when fetching session data fails (e.g., the session ID is invalid or expired).
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session for which data retrieval failed.<br>``reason`` (:py:class:`str`): A short string explaining the failure (e.g., "not_found_or_expired").
   * - ``session_data_saved``
     - Emitted when the session's data payload (the dictionary stored in the 'data' column) is successfully updated in the database.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session whose data was saved.<br>``saved_keys`` (:py:class:`list` of :py:class:`str`): A list of the top-level keys in the dictionary that was saved.
   * - ``session_data_save_failed``
     - Emitted when an attempt to save session data encounters an error.
     - ``sender`` (:py:class:`~lback.utils.session_manager.SessionManager`): The session manager instance.<br>``session_id`` (:py:class:`str`): The ID of the session for which data saving failed.<br>``reason`` (:py:class:`str`): A short string explaining the failure (e.g., "not_found", "serialization_error_or_db_error").<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was caused by an error.
