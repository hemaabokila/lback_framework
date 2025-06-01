import json
import os
import importlib.util
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import logging


logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"
SETTINGS_MODULE_NAME = "project_settings"
ENCRYPTED_KEYS = [
    "DB_PASSWORD_ENCRYPTED",
    "API_KEY_SERVICE_1_ENCRYPTED",
    "API_KEY_SERVICE_2_ENCRYPTED",
    "EMAIL_PASSWORD_ENCRYPTED",
]


def load_settings_module(settings_path):
    """Dynamically loads/reloads a Python file as a module."""
    if not os.path.exists(settings_path):
        logger.warning(f"Settings file not found at {settings_path}")
        return None
    try:
        spec = importlib.util.spec_from_file_location(SETTINGS_MODULE_NAME, settings_path)
        settings = importlib.util.module_from_spec(spec)
        if SETTINGS_MODULE_NAME in sys.modules:
             logger.debug(f"Reloading existing settings module: {SETTINGS_MODULE_NAME}")
             importlib.reload(sys.modules[SETTINGS_MODULE_NAME])
             settings = sys.modules[SETTINGS_MODULE_NAME]
        else:
             logger.debug(f"Loading settings module for the first time: {SETTINGS_MODULE_NAME}")
             sys.modules[SETTINGS_MODULE_NAME] = settings
             spec.loader.exec_module(settings)

        logger.debug(f"Successfully loaded/reloaded settings module from {settings_path}")
        return settings
    except Exception as e:
        logger.error(f"Error loading settings module from {settings_path}: {e}", exc_info=True)
        if SETTINGS_MODULE_NAME in sys.modules:
             del sys.modules[SETTINGS_MODULE_NAME]
        return None


def load_config(config_file=CONFIG_FILE):
    """Load configuration from JSON file. This is mainly for reading existing config before updating."""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                logger.debug(f"Loading existing config from {config_file}")
                return json.load(f)
        except json.JSONDecodeError as e:
             logger.error(f"Error decoding JSON from {config_file}: {e}. Returning empty config.", exc_info=True)
             return {}
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}. Returning empty config.", exc_info=True)
            return {}
    else:
        logger.debug(f"Config file not found at {config_file}. Returning empty config.")
        return {}

def update_config(new_config, config_file=CONFIG_FILE):
    """Update config.json with new values and save."""
    try:
        config_dir = os.path.dirname(config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
            logger.debug(f"Created directory for config file: {config_dir}")

        with open(config_file, 'w') as f:
            json.dump(new_config, f, indent=4)
        logger.debug(f"Successfully updated config file: {config_file}")
    except Exception as e:
        logger.error(f"Error writing config file {config_file}: {e}", exc_info=True)


def sync_settings_to_config(settings_path, config_file=CONFIG_FILE):
    """Reads settings from settings.py and syncs them to config.json."""
    logger.info(f"Syncing settings from {settings_path} to {config_file}...")
    settings = load_settings_module(settings_path)
    if settings is None:
        logger.warning("Failed to load settings module. Cannot sync config.")
        return

    settings_dict = {}
    for attr_name in dir(settings):
        if attr_name.isupper() and not attr_name.startswith('_'):
            try:
                value = getattr(settings, attr_name)
                try:
                    json.dumps(value)
                    settings_dict[attr_name] = value
                    logger.debug(f"Read and included setting: {attr_name}")
                except TypeError:
                    logger.warning(f"Setting '{attr_name}' has a non-JSON serializable type ({type(value).__name__}). Skipping sync to config.json.")

            except Exception as e:
                logger.warning(f"Could not read setting {attr_name} from settings module: {e}")
    try:
        from cryptography.fernet import Fernet
        encryption_key_for_validation = settings_dict.get("ENCRYPTION_KEY") or os.getenv("ENCRYPTION_KEY")

        fernet_check = None
        if not encryption_key_for_validation:
             logger.warning("ENCRYPTION_KEY not found in loaded settings or environment during config sync check. Cannot validate encrypted strings.")
             
        else:
             try:
                 key_bytes = encryption_key_for_validation.encode()
                 fernet_check = Fernet(key_bytes)
                 logger.debug("Fernet cipher initialized for sync-time validation.")
             except Exception as e:
                 logger.warning(f"Invalid ENCRYPTION_KEY found for sync-time validation: {e}. Cannot validate encrypted strings.")
                 fernet_check = None
        for key in ENCRYPTED_KEYS:
            value = settings_dict.get(key)
            if value and isinstance(value, str):
                if value.startswith("gAAAAAB"):
                    if fernet_check:
                        try:
                            fernet_check.decrypt(value.encode(), ttl=1)
                            logger.debug(f"Test decryption succeeded for '{key}' (sync check).")
                        except Exception as e:
                            logger.warning(f"Test decryption FAILED for '{key}' value from settings.py using the available ENCRYPTION_KEY: {e}. This value may be invalid or encrypted with a different key.")
                    else:
                        logger.debug(f"Skipping decryption test for '{key}' as no valid ENCRYPTION_KEY is available for sync check.")
                else:
                    logger.warning(f"Value for '{key}' in settings.py is a string but does NOT look like a Fernet token. Decryption during runtime will likely fail if this value is used.")
            elif value is not None:
                 logger.debug(f"Value for '{key}' is not a string ({type(value).__name__}). Skipping Fernet token format check.")

    except ImportError:
        logger.warning("Cryptography or dotenv not installed. Cannot perform encrypted string validation during config sync.")
    except Exception as e:
         logger.warning(f"An unexpected error occurred during encrypted string validation in config sync: {e}", exc_info=True)

    update_config(settings_dict, config_file)
    logger.info("Config sync complete.")

class SettingsFileHandler(FileSystemEventHandler):
    """Handles file system events for settings.py."""
    def __init__(self, settings_path, config_file=CONFIG_FILE):
        self.settings_path = settings_path
        self.config_file = config_file
        logger.debug(f"Initialized SettingsFileHandler for {settings_path}")
        self._sync_lock = threading.Lock()

    def on_modified(self, event):
        """Called when a file is modified."""
        normalized_event_path = os.path.abspath(event.src_path)
        normalized_settings_path = os.path.abspath(self.settings_path)

        if normalized_event_path == normalized_settings_path:
             logger.info(f"Change detected in {event.src_path}. Syncing config...")
             with self._sync_lock:
                 time.sleep(0.5)
                 try:
                     sync_settings_to_config(self.settings_path, self.config_file)
                 except Exception as e:
                      logger.error(f"Error during config sync triggered by file modification: {e}", exc_info=True)


def start_settings_watcher(project_root):
    """Starts the file system watcher for settings.py."""
    settings_path = os.path.join(project_root, "settings.py")
    config_file = os.path.join(project_root, CONFIG_FILE)

    if not os.path.exists(settings_path):
        logger.warning(f"settings.py not found at {settings_path}. Settings watcher will not start.")
        return

    logger.info("Performing initial sync from settings.py to config.json.")
    try:
         sync_settings_to_config(settings_path, config_file)
    except Exception as e:
         logger.error(f"Error during initial config sync: {e}", exc_info=True)

    settings_dir = os.path.dirname(settings_path)
    if not os.path.exists(settings_dir):
         logger.error(f"Directory containing settings.py not found: {settings_dir}")
         return

    event_handler = SettingsFileHandler(settings_path, config_file)
    observer = Observer()
    observer.schedule(event_handler, path=settings_dir, recursive=False)
    observer_thread = threading.Thread(target=observer.start, daemon=True)
    observer_thread.start()
    logger.info(f"Watching {settings_path} for changes...")



def get_project_root():
    """Finds the project root directory by searching for settings.py."""
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.exists(os.path.join(current, "settings.py")):
            logger.debug(f"Found project root from CWD: {current}")
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    script_dir = os.path.dirname(os.path.abspath(__file__))
    current = script_dir
    logger.debug(f"settings.py not found from CWD. Searching from script directory: {script_dir}")
    while True:
        if os.path.exists(os.path.join(current, "settings.py")):
            logger.debug(f"Found project root from script directory: {current}")
            return current
        parent = os.path.dirname(current)
        if parent == current:
             break
        current = parent
    raise FileNotFoundError("settings.py not found in any parent directory from current working directory or script location.")
