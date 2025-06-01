File Uploads in Lback Framework
===============================

Handling file uploads is a fundamental part of many web applications. Lback provides a robust and flexible way to manage file uploads, including validation and secure storage.

---

1. How File Uploads Work in Lback
---------------------------------

The file upload process relies on several core components working seamlessly together:

* ``BodyParsingMiddleware``: (in ``lback/middlewares/body_parsing_middleware.py``)
    This middleware is responsible for parsing the request body when the ``Content-Type`` is ``multipart/form-data``. It transforms uploaded files into ``UploadedFile`` objects and makes them accessible via ``request.files``.
* ``UploadedFile`` **Class**: (in ``lback/core/types.py``)
    This object represents an uploaded file. It holds useful properties such as ``filename`` (the original file name), ``content_type`` (MIME type), ``size`` (size in bytes), and ``file`` (a file-like object representing the file's content).
* ``file_handlers.py`` **Utilities**: (in ``lback/utils/file_handlers.py``)
    This file contains helper functions to streamline file processing:
    * ``validate_uploaded_file()``: Checks the file's type and size against specified rules.
    * ``save_uploaded_file()``: Saves the uploaded file to a structured directory on the file system.
    * ``delete_saved_file()``: Deletes a previously saved file.
* **Generic Admin Panel (and your custom controllers)**:
    These components (like the Generic Add View or Generic Edit View) leverage the ``file_handlers`` functions to automatically process files uploaded from HTML forms.

**The Workflow:**

1.  When a user submits an HTML form containing an ``<input type="file">`` field, the request is sent as ``multipart/form-data``.
2.  The `BodyParsingMiddleware` intercepts and parses this request, extracting the uploaded files.
3.  Each uploaded file is converted into an ``UploadedFile`` object and stored in ``request.files`` (which is a ``MultiDict``, allowing for multiple files under the same field name).
4.  In your View or Controller (whether it's a Generic Admin View or your custom view):
    * You can access uploaded files via `request.files`.
    * You can call ``validate_uploaded_file()`` to check the file's integrity before saving.
    * You can call ``save_uploaded_file()`` to store the file in the correct location on the server.
    * The saved file paths (relative paths) are what you should store in your database.

---

2. File Upload Configuration Options in ``settings.py``
----------------------------------------------------

You can customize file upload behavior by configuring the following settings in your project's ``settings.py`` file:

* **UPLOAD_FOLDER**: (Optional, default is ``uploads``) The name of the base directory within your project where all uploaded files will be stored.
    * **Example:** ``UPLOAD_FOLDER = 'static/uploads'``
* **UPLOAD_ALLOWED_TYPES**: (Optional, default is ``None`` which allows all types) A list of allowed MIME types for uploaded files.
    * **Example:** ``UPLOAD_ALLOWED_TYPES = ['image/jpeg', 'image/png', 'application/pdf']``
* **UPLOAD_MAX_SIZE_MB**: (Optional, default is ``None`` for no size limit) The maximum allowed size for uploaded files in megabytes.
    * **Example:** ``UPLOAD_MAX_SIZE_MB = 5`` (maximum size of 5 MB)

---

3. How to Handle Uploaded Files in Views
----------------------------------------

Once ``BodyParsingMiddleware`` parses the request, uploaded files will be available in ``request.files`` as ``UploadedFile`` objects.

#### Examples:

1.  **Accessing a Single Uploaded File:**
    If you expect a single file for a specific field (e.g., ``profile_picture``):

    .. code-block:: python

        # In your View or Controller
        from lback.core.types import Request, UploadedFile
        from lback.utils.file_handlers import save_uploaded_file, validate_uploaded_file
        from lback.core.config import Config # Ensure Config or current_app.config is imported

        def upload_profile_picture(request: Request):
            # Assume you have a Config object available here, perhaps from request.app.config
            config: Config = request.app.config # Or the appropriate way to access app configuration

            # Access the uploaded file
            profile_pic_file: Optional[UploadedFile] = request.files.get('profile_picture')

            if profile_pic_file:
                # Pass the `model_name` under which you want to save the files (typically the model/entity name)
                # and the validation settings defined in your config
                saved_path = save_uploaded_file(
                    profile_pic_file,
                    config=config,
                    model_name='users', # E.g., 'users' folder within UPLOAD_FOLDER
                    allowed_types=config.UPLOAD_ALLOWED_TYPES,
                    max_size_mb=config.UPLOAD_MAX_SIZE_MB
                )

                if saved_path:
                    # File saved successfully!
                    # You can now store 'saved_path' in your database (e.g., 'profile_picture_path' column in the User table)
                    # user.profile_picture_path = saved_path
                    # db_session.add(user)
                    # db_session.commit()
                    request.session['flash_messages'].append({'message': f"Profile picture uploaded successfully: {saved_path}", 'category': 'success'})
                    return redirect('/profile')
                else:
                    # Save failed, check for validation errors
                    error_message = validate_uploaded_file(profile_pic_file, config.UPLOAD_ALLOWED_TYPES, config.UPLOAD_MAX_SIZE_MB)
                    if not error_message: # If no specific validation error, the error was during the save operation
                        error_message = "Failed to save profile picture due to an unexpected error."
                    request.session['flash_messages'].append({'message': error_message, 'category': 'error'})
                    return redirect('/upload-form')
            else:
                request.session['flash_messages'].append({'message': 'No profile picture file was provided.', 'category': 'warning'})
                return redirect('/upload-form')

2.  **Handling Multiple Files for the Same Field (** ``multiple`` **attribute in HTML):**
    If you have a multi-file input field (e.g., ``gallery_images[]``):

    .. code-block:: python

        # In your View or Controller
        from typing import List
        # ... (same previous imports) ...

        def upload_gallery_images(request: Request):
            config: Config = request.app.config

            # request.files.getlist() returns a list of objects for a given field name
            gallery_files: List[UploadedFile] = request.files.getlist('gallery_images')

            uploaded_paths = []
            errors = []

            if gallery_files:
                for file_obj in gallery_files:
                    if isinstance(file_obj, UploadedFile):
                        saved_path = save_uploaded_file(
                            file_obj,
                            config=config,
                            model_name='gallery', # 'gallery' folder
                            allowed_types=config.UPLOAD_ALLOWED_TYPES,
                            max_size_mb=config.UPLOAD_MAX_SIZE_MB
                        )
                        if saved_path:
                            uploaded_paths.append(saved_path)
                            # Now you can save 'saved_path' to your database, perhaps in an Image table related to Gallery
                        else:
                            error_message = validate_uploaded_file(file_obj, config.UPLOAD_ALLOWED_TYPES, config.UPLOAD_MAX_SIZE_MB)
                            if not error_message:
                                error_message = f"Failed to save {file_obj.filename} due to an unexpected error."
                            errors.append(f"Error with {file_obj.filename}: {error_message}")
                    else:
                        errors.append(f"Unexpected file object type for {file_obj.filename}.")
            else:
                errors.append("No gallery images were provided.")

            if uploaded_paths:
                request.session['flash_messages'].append({'message': f"Successfully uploaded {len(uploaded_paths)} images.", 'category': 'success'})
            if errors:
                for err in errors:
                    request.session['flash_messages'].append({'message': err, 'category': 'error'})

            return redirect('/gallery')

3.  **Deleting a Saved File:**

    .. code-block:: python

        # In your View or Controller
        from lback.utils.file_handlers import delete_saved_file
        # ... (same previous imports) ...

        def delete_image(request: Request):
            image_relative_path = request.form.get('image_path') # Assume the path comes from the form
            config: Config = request.app.config

            if image_relative_path:
                if delete_saved_file(image_relative_path, config=config):
                    # File successfully deleted from the file system
                    # Now, delete the path from your database
                    # image_record = db_session.query(Image).filter_by(path=image_relative_path).first()
                    # if image_record:
                    #     db_session.delete(image_record)
                    #     db_session.commit()
                    request.session['flash_messages'].append({'message': "Image deleted successfully.", 'category': 'success'})
                    return redirect('/admin/images')
                else:
                    request.session['flash_messages'].append({'message': "Failed to delete image from server.", 'category': 'error'})
                    return redirect('/admin/images')
            else:
                request.session['flash_messages'].append({'message': "No image path provided for deletion.", 'category': 'warning'})
                return redirect('/admin/images')