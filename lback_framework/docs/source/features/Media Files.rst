Media Files
===========

Media files are user-uploaded content, such as profile pictures, document uploads, or video files.

framework provides tools to manage these dynamic assets, making it easy to store and serve user-generated content.

Configuration
-------------

Set up the storage location and URL path for your media files in ``settings.py``:

    .. code-block:: python
        
        # settings.py
        import os

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        UPLOAD_FOLDER = 'media/uploads' # The directory where uploaded files will be stored
        UPLOAD_URL = '/media/uploads/' # The URL path for accessing uploaded files

        PROJECT_ROOT = BASE_DIR # Typically the same as BASE_DIR

Usage in Templates
------------------

Similar to static files, you can reference your media files in templates.

If your model has a field storing the path to an uploaded file (e.g., ``user.profile_picture_path``), you can construct the URL using the ``UPLOAD_URL`` from your settings or a helper function if available:

    .. code-block:: html
        
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ user.username }} Profile</title>
        </head>
        <body>
            <h1>{{ user.username }}'s Profile</h1>
            {% if user.profile_picture_path %}
                <img src="{{ config.UPLOAD_URL }}{{ user.profile_picture_path }}" alt="Profile Picture" width="150">
            {% else %}
                <p>No profile picture uploaded.</p>
            {% endif %}

            <p>Bio: {{ user.bio }}</p>
        </body>
        </html>
