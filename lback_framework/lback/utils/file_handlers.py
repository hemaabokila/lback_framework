import logging
import os
import uuid
from typing import Optional, List
from datetime import datetime 
import magic

from lback.core.types import UploadedFile
from lback.core.config import Config

logger = logging.getLogger(__name__)

def validate_uploaded_file(uploaded_file: UploadedFile, allowed_types: Optional[List[str]] = None, max_size_mb: Optional[int] = None) -> Optional[str]:
    """
    Validates an uploaded file based on allowed types and maximum size.

    Args:
        uploaded_file: The UploadedFile object.
        allowed_types: A list of allowed MIME types (e.g., ['image/jpeg', 'image/png']).
                       If None, all types are allowed.
        max_size_mb: Maximum allowed file size in megabytes. If None, no size limit.

    Returns:
        None if validation succeeds, otherwise a string with an error message.
    """
    if not uploaded_file or not uploaded_file.file:
        return "No file uploaded."

    if max_size_mb is not None:
        max_size_bytes = max_size_mb * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            return f"File size exceeds the maximum allowed size of {max_size_mb} MB."

    if allowed_types:
        try:
            uploaded_file.file.seek(0)
            mime_type = magic.from_buffer(uploaded_file.file.read(1024), mime=True)
            uploaded_file.file.seek(0)

            logger.debug(f"validate_uploaded_file: Detected MIME type for '{uploaded_file.filename}': {mime_type}")

            if mime_type not in allowed_types:
                return f"File type '{mime_type}' is not allowed. Allowed types are: {', '.join(allowed_types)}"
        except Exception as e:
            logger.error(f"validate_uploaded_file: Error detecting MIME type for '{uploaded_file.filename}': {e}", exc_info=True)
            return f"Could not determine file type for validation."

    return None

def save_uploaded_file(uploaded_file: UploadedFile, config: Config, model_name: str, allowed_types: Optional[List[str]] = None, max_size_mb: Optional[int] = None) -> Optional[str]:
    """
    Saves an uploaded file to the server's file system.
    Determines save path based on config and model name.
    Returns the relative path to the saved file, or None on failure.
    """
    if not uploaded_file or not uploaded_file.file:
        logger.warning("save_uploaded_file: No file or file stream provided.")
        return None
    
    validation_error = validate_uploaded_file(uploaded_file, allowed_types, max_size_mb)
    if validation_error:
        logger.warning(f"save_uploaded_file: File validation failed for '{uploaded_file.filename}': {validation_error}")
        uploaded_file.close()
        return None
    upload_folder_config_value = getattr(config, 'UPLOAD_FOLDER', 'uploads')
    project_root = getattr(config, 'PROJECT_ROOT', os.getcwd()) 
    full_upload_dir = os.path.join(project_root, upload_folder_config_value)

    try:
        os.makedirs(full_upload_dir, exist_ok=True)
        logger.debug(f"save_uploaded_file: Base upload directory is {full_upload_dir}")
    except Exception as e:
        logger.error(f"save_uploaded_file: Failed to create base upload directory {full_upload_dir}: {e}", exc_info=True)
        uploaded_file.close() 
        return None

    sub_folder = model_name.lower()
    now = datetime.now()
    date_sub_folder = now.strftime('%Y/%m/%d')
    
    save_dir = os.path.join(full_upload_dir, sub_folder, date_sub_folder)

    try:
        os.makedirs(save_dir, exist_ok=True)
        logger.debug(f"save_uploaded_file: Save directory is {save_dir}")
    except Exception as e:
        logger.error(f"save_uploaded_file: Failed to create save directory {save_dir}: {e}", exc_info=True)
        uploaded_file.close() 
        return None

    file_extension = os.path.splitext(uploaded_file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    full_save_path = os.path.join(save_dir, unique_filename)
    logger.debug(f"save_uploaded_file: Full save path will be {full_save_path}")

    try:
        uploaded_file.file.seek(0)
        with open(full_save_path, 'wb') as f:
            f.write(uploaded_file.file.read())
        
        logger.info(f"save_uploaded_file: Successfully saved file to {full_save_path}")

        relative_path = os.path.relpath(full_save_path, start=full_upload_dir)
        relative_path = relative_path.replace(os.sep, '/')

        logger.debug(f"save_uploaded_file: Relative path to store in DB: {relative_path}")
        
        return relative_path

    except Exception as e:
        logger.error(f"save_uploaded_file: Error saving file {uploaded_file.filename}: {e}", exc_info=True)
        return None
    finally:
        uploaded_file.close()

def delete_saved_file(relative_file_path: str, config: Config) -> bool:
    """
    Deletes a saved file from the server's file system based on its relative path.
    Returns True if successful, False otherwise.
    """
    if not relative_file_path:
        logger.warning("delete_saved_file: No relative file path provided.")
        return False

    upload_folder = getattr(config, 'UPLOAD_FOLDER', 'uploads')
    project_root = getattr(config, 'PROJECT_ROOT', os.getcwd())
    
    full_upload_dir = os.path.join(project_root, upload_folder) 
    
    full_file_path = os.path.join(full_upload_dir, relative_file_path)

    if not os.path.abspath(full_file_path).startswith(os.path.abspath(full_upload_dir)):
        logger.warning(f"delete_saved_file: Attempted directory traversal detected for path: {relative_file_path}")
        return False
        
    if not os.path.isfile(full_file_path):
        logger.warning(f"delete_saved_file: File not found at path: {full_file_path}")
        return False
        
    try:
        os.remove(full_file_path)
        logger.info(f"delete_saved_file: Successfully deleted file at {full_file_path}")
        return True
    except Exception as e:
        logger.error(f"delete_saved_file: Error deleting file at {full_file_path}: {e}", exc_info=True)
        return False
