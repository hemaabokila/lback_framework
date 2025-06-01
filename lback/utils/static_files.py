import os
import logging
from typing import List, Optional, Any 

logger = logging.getLogger(__name__)

def static(config: Any, relative_path: str) -> str:
    """
    Generates the full URL for a static file.

    Args:
        config: The application's configuration object, expected to have a STATIC_URL attribute.
        relative_path: The path to the static file relative to the static directories (e.g., 'css/style.css').

    Returns:
        The full URL to the static file (e.g., '/static/css/style.css').
        Returns the relative_path itself if STATIC_URL is not configured.
    """
    static_url = getattr(config, 'STATIC_URL', None)
    if static_url:
        static_url = static_url.rstrip('/') + '/'
        relative_path = relative_path.lstrip('/')
        full_url_path = os.path.join(static_url, relative_path).replace(os.sep, '/')
        logger.debug(f"Generated static URL for '{relative_path}': {full_url_path}")
        return full_url_path
    else:
        logger.warning("STATIC_URL is not configured in config. Returning relative path for static file.")
        return relative_path


def find_static_file(config: Any, relative_path: str) -> Optional[str]:
    """
    Finds the absolute file system path for a static file by searching in STATIC_DIRS.

    Args:
        config: The application's configuration object, expected to have STATIC_DIRS and PROJECT_ROOT attributes.
        relative_path: The path to the static file relative to the static directories (e.g., 'css/style.css').

    Returns:
        The absolute file system path to the static file, or None if not found.
    """
    static_dirs: Optional[List[str]] = getattr(config, 'STATIC_DIRS', None)
    project_root = getattr(config, 'PROJECT_ROOT', os.getcwd())

    if not static_dirs:
        logger.warning("STATIC_DIRS is not configured in config. Cannot find static file.")
        return None

    relative_path = relative_path.lstrip('/')

    for static_dir in static_dirs:
        full_static_dir = os.path.join(project_root, static_dir)
        full_file_path = os.path.join(full_static_dir, relative_path)
        full_file_path = os.path.normpath(full_file_path)

        is_within_static_dir = False
        try:
            abs_full_file_path = os.path.abspath(full_file_path)
            abs_full_static_dir = os.path.abspath(full_static_dir)
            if abs_full_file_path.startswith(abs_full_static_dir):
                 is_within_static_dir = True
            else:
                 logger.warning(f"find_static_file: Directory traversal attempt detected. Resolved path '{abs_full_file_path}' is outside static directory '{abs_full_static_dir}'.")
                 continue

        except Exception as e:
             logger.error(f"find_static_file: Error performing path checks for '{full_file_path}': {e}", exc_info=True)
             continue

        if is_within_static_dir and os.path.isfile(full_file_path):
            logger.debug(f"find_static_file: Found static file at {full_file_path}")
            return full_file_path
        
    logger.warning(f"find_static_file: Static file '{relative_path}' not found in any configured STATIC_DIRS.")
    return None

