Sessions in Lback Framework
===========================

Sessions provide a way to store user-specific data across multiple HTTP requests. In Lback, **Database Sessions** are used, meaning session data is persistently stored in your database, offering greater flexibility and stability.

---

1. Session Structure in the Database
-----------------------------------

Session data is stored in a ``Session`` table in your database (typically ``db.sqlite`` if you're using SQLite). This table primarily consists of the following columns:

* ``id``: A unique identifier for the session (usually a UUID). This is the ``session_id`` sent to the browser in the Cookie.
* ``user_id``: (Optional) The ID of the user associated with this session. This column is dedicated to directly linking a session to a specific user in your ``users`` table.
* ``data``: **The most important column.** This stores all the actual session data (e.g., shopping cart contents, login status, flash messages). This data is stored as a **JSON** string (a `TEXT` type in the database).
* ``expires_at``: The date and time when the session expires. This date is automatically renewed with each request.
* ``created_at``: The date and time when the session was first created.
* ``updated_at``: The date and time of the last update to the session.

---

2. How Sessions Work in Lback
-----------------------------

Session management in Lback relies on two core components:

* ``SessionMiddleware``: This middleware (located in ``lback/middlewares/session_middleware.py``) is responsible for:
    * **Reading the Session ID from a cookie** at the beginning of each request.
    * **Fetching session data from the database** using the ``SessionManager``.
    * **Placing an ``AppSession`` object** (the session wrapper) into the request context (``request.context['session']``) for easy access by your views.
    * **Saving modified session data back to the database** at the end of the request (if changes occurred).
    * **Setting or deleting the session cookie** in the browser's response.

* ``SessionManager``: This class (located in ``lback/utils/session_manager.py``) directly interacts with the database to:
    * Create new sessions.
    * Retrieve existing session data.
    * Update session data.
    * Renew session expiration.
    * Delete sessions.

**The Workflow:**

1.  When an HTTP request arrives, ``SQLAlchemyMiddleware`` first sets up a database session (``db_session``).
2.  Next, ``SessionMiddleware`` inspects the request for a ``session_id`` cookie.
3.  If no ``session_id`` is found or it's invalid/expired, it's treated as a new session, and a new ``session_id`` is generated and stored in the database by ``SessionManager``.
4.  If a valid ``session_id`` exists, ``SessionMiddleware`` retrieves the associated session data from the database.
5.  In either case, an ``AppSession`` object (which wraps the session data and associated logic) is initialized and made available via ``request.context['session']``.
6.  Your views and controllers can now interact with ``request.session``.
7.  After the request is processed by your view, and before the response is sent back to the browser, ``SessionMiddleware`` saves any changes made to ``request.session`` back to the database and updates the session cookie in the response.

---

3. Session Configuration Options in ``settings.py``
------------------------------------------------

You can customize session behavior by configuring the following settings in your project's ``settings.py`` file:

* ``SESSION_TIMEOUT_MINUTES``: (Required) Specifies how long a session remains valid (in minutes) if there's no activity. The session's expiration is automatically renewed with each request made within this period.

    * **Example:** ``SESSION_TIMEOUT_MINUTES = 30`` (session expires after 30 minutes of inactivity).

* ``SESSION_COOKIE_NAME``: (Optional, default is ``session_id``) The name of the cookie used to store the session ID in the user's browser.

    * **Example:** ``SESSION_COOKIE_NAME = 'my_app_session_id'``

---

4. Accessing and Storing Session Data in Views
-----------------------------------------------

Once ``SessionMiddleware`` makes the ``AppSession`` object available in ``request.context['session']``, developers can easily access and manipulate session data within their views (or controllers).

``request.session`` behaves like a dictionary-like object, allowing for straightforward data storage and retrieval.

**Examples:**

1.  **Storing data in the Session:**

    .. code-block:: python

        # In your View or Controller
        def login_view(request: Request):
            # ... (after successful login credential verification) ...
            user = get_user_by_credentials(request.form)
            if user:
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                request.session['is_authenticated'] = True
                request.session['flash_messages'] = [{'message': 'Welcome back!', 'category': 'success'}]
                # All this data will be automatically saved to the database at the end of the request
                return redirect('/')
            # ...

2.  **Accessing data from the Session:**

    .. code-block:: python

        # In your View or Controller
        def profile_view(request: Request):
            user_id = request.session.get('user_id')
            username = request.session.get('username')

            if user_id and username:
                # Load user data from the database using user_id
                # ...
                return render_template('profile.html', user_id=user_id, username=username)
            else:
                # User not logged in or data not in session
                request.session['flash_messages'] = [{'message': 'Please log in to view your profile.', 'category': 'warning'}]
                return redirect('/login')

        def display_flash_messages(request: Request):
            # Typically called in the base template
            messages = request.session.get('flash_messages', [])
            # After displaying messages, they should be cleared so they don't reappear
            if messages:
                request.session['flash_messages'] = [] # Clear messages after reading them
            return messages

3.  **Checking if the Session is New:**

    .. code-block:: python

        if request.session.is_new:
            print("This is a new user session.")

4.  **Checking if the Session has been Modified:**

    .. code-block:: python

        if request.session.modified:
            print("Session data has been modified and will be saved to the database.")

5.  **Deleting Specific Data from the Session:**

    .. code-block:: python

        # To delete a single item
        if 'item_in_cart' in request.session:
            del request.session['item_in_cart']

        # Or clear all current session data while keeping the session itself
        # (This does not delete the Session from the database, only its contents)
        request.session.clear()

6.  **Deleting the Entire Session (Logout):**

    .. code-block:: python

        def logout_view(request: Request):
            request.session.delete() # Deletes the session from the database and removes the cookie
            request.session['flash_messages'] = [{'message': 'You have been logged out.', 'category': 'info'}]
            return redirect('/')

---

By following these guidelines, you will be able to effectively manage sessions in your Lback-based applications.