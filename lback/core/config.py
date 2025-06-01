import os
from cryptography.fernet import Fernet
import logging
import json
import yaml

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

DEFAULTS = {
    "SECRET_KEY": Fernet.generate_key().decode(),
    "ENCRYPTION_KEY": Fernet.generate_key().decode(),
    "DB_ENGINE": "sqlite",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "admin",
    "DB_PASSWORD_ENCRYPTED": "",
    "DB_NAME": "db",
    "DATABASE_ECHO": "False",
    "API_KEY_SERVICE_1_ENCRYPTED": "",
    "API_KEY_SERVICE_2_ENCRYPTED": "",
    "JWT_SECRET_KEY": "",
    "SMTP_SERVER": "",
    "SMTP_PORT": "587",
    "EMAIL_USERNAME": "",
    "EMAIL_PASSWORD": "",
    "DEBUG": "True",
    "ALLOWED_HOSTS": [],
    "API_VERSION": "v1",
    "LOGGING_LEVEL": "DEBUG",
    "INSTALLED_APPS": [],
    "MIDDLEWARES": [],
    "ROOT_URLCONF": None,
    "USE_TLS": "True",
    "SENDER_NAME": "",
    "SENDER_EMAIL": "",
    "PROJECT_SETTINGS_MODULE": "settings",
}



def load_config(config_file=CONFIG_FILE):
    """Load configuration from JSON or YAML file."""
    if os.path.exists(config_file):
        logger.info(f"Loading configuration from {config_file}")
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    return json.load(f)
                elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    logger.warning(f"Unsupported config file format for {config_file}. Only .json, .yaml, .yml are supported.")
                    return {}
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}", exc_info=True)
            return {}
    else:
        logger.info(f"No config file found at {config_file}. Relying on environment variables and defaults.")
        return {}


class Config:
    """
    Manages application configuration, loading with priority:
    Environment Variables -> Config File -> Defaults.
    Provides access to settings and generates derived values.
    """
    def __init__(self, config_file=CONFIG_FILE):
        """
        Intializes a Config instance by loading configuration data
        with priority Environment -> ConfigFile -> Defaults.
        Assumes environment variables (e.g., from .env) are already loaded.
        """
        logger.info(f"Config instance initialized. Attempting to load configuration from {config_file}, environment, and defaults.")

        loaded_config_data = load_config(config_file)

        def _get_value(key, conversion_func=None, default=None):
            """Helper to get a config value with priority: Env -> ConfigFile -> specified default -> DEFAULTS default."""
            env_value = os.getenv(key)
            if env_value is not None:
                 if conversion_func:
                     try:
                         return conversion_func(env_value)
                     except (ValueError, TypeError) as e:
                         logger.warning(f"Failed to convert environment variable '{key}' value '{env_value}' using {getattr(conversion_func, '__name__', 'conversion_func')}: {e}. Falling back to config file or default.")
                         pass
                 else:
                     return env_value


            config_value = loaded_config_data.get(key)
            if config_value is not None:
                if conversion_func:
                    try:
                        return conversion_func(config_value)
                    except (ValueError, TypeError) as e:
                         logger.warning(f"Failed to convert config file value for '{key}' value '{config_value}' using {getattr(conversion_func, '__name__', 'conversion_func')}: {e}. Falling back to default.")
                         pass
                else:
                    return config_value


            if default is not None:
                 if conversion_func:
                      try:
                          return conversion_func(default)
                      except (ValueError, TypeError) as e:
                           logger.error(f"Failed to convert explicit default value for '{key}' value '{default}' using {getattr(conversion_func, '__name__', 'conversion_func')}: {e}. Using raw explicit default.")
                           return default
                 else:
                      return default

            default_value_from_defaults = DEFAULTS.get(key)
            if default_value_from_defaults is not None:
                if conversion_func:
                    try:
                        return conversion_func(default_value_from_defaults)
                    except (ValueError, TypeError) as e:
                         logger.error(f"Failed to convert DEFAULTS value for '{key}' value '{default_value_from_defaults}' using {getattr(conversion_func, '__name__', 'conversion_func')}: {e}. Using raw DEFAULTS value.")
                         return default_value_from_defaults
                else:
                    return default_value_from_defaults

            return None

        def _str_to_bool(value):
             if value is None: return None
             if isinstance(value, bool): return value
             return str(value).lower() in ("true", "1", "t")

        def _to_int(value):
             if value is None: return None
             if isinstance(value, int): return value
             try:
                 return int(str(value))
             except (ValueError, TypeError):
                 logger.warning(f"Could not convert value '{value}' to integer.")
                 return None

        def _to_list(value):
            if value is None: return None
            if isinstance(value, list): return value
            if isinstance(value, str):
                return [item.strip() for item in value.split(',') if item.strip()]
            logger.warning(f"Could not convert value '{value}' to list.")
            return None


        encryption_key_str = _get_value("ENCRYPTION_KEY", default=DEFAULTS["ENCRYPTION_KEY"])

        self.fernet = None
        if not encryption_key_str:
             logger.error("ENCRYPTION_KEY not found in environment, config file, or defaults. Cannot initialize Fernet cipher.")
        else:
            try:
                key_bytes = encryption_key_str.encode()
                if len(key_bytes) != 44:
                     logger.error("Invalid ENCRYPTION_KEY format (incorrect length). Must be 32 url-safe base64 bytes (44 characters).")
                     self.fernet = None
                else:
                    self.fernet = Fernet(key_bytes)
                    logger.info("Fernet cipher initialized.")
            except Exception as e:
                 logger.error(f"Error initializing Fernet cipher with ENCRYPTION_KEY: {e}", exc_info=True)

        def decrypt_instance(data):
             """Decrypts data using the instance's Fernet cipher."""
             if data is None or data == "":
                 return None
             if isinstance(data, str):
                  data_bytes = data.encode()
             elif isinstance(data, bytes):
                  data_bytes = data
             else:
                  return None

             if self.fernet is None:
                 return None

             try:
                 return self.fernet.decrypt(data_bytes).decode()
             except Exception as e:
                 return None
        self.decrypt = decrypt_instance


        self.SECRET_KEY = _get_value("SECRET_KEY", default=DEFAULTS["SECRET_KEY"])

        self.DEBUG = _get_value("DEBUG", conversion_func=_str_to_bool, default=DEFAULTS["DEBUG"])
        if self.DEBUG is None: self.DEBUG = _str_to_bool(DEFAULTS["DEBUG"]) if "DEBUG" in DEFAULTS else False

        self.API_VERSION = _get_value("API_VERSION", default=DEFAULTS["API_VERSION"])

        logging_level_val = _get_value("LOGGING_LEVEL", default=DEFAULTS["LOGGING_LEVEL"])
        self.LOGGING_LEVEL = str(logging_level_val).upper() if logging_level_val is not None else DEFAULTS["LOGGING_LEVEL"].upper()

        db_engine_val = _get_value("DB_ENGINE", default=DEFAULTS["DB_ENGINE"])
        self.DB_ENGINE = str(db_engine_val).lower() if db_engine_val is not None else DEFAULTS["DB_ENGINE"].lower()

        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

        self.INSTALLED_APPS = _get_value("INSTALLED_APPS", conversion_func=_to_list, default=DEFAULTS["INSTALLED_APPS"])
        if not isinstance(self.INSTALLED_APPS, list): self.INSTALLED_APPS = []

        self.DATABASE_ECHO = _get_value("DATABASE_ECHO", conversion_func=_str_to_bool, default=DEFAULTS["DATABASE_ECHO"])
        if self.DATABASE_ECHO is None: self.DATABASE_ECHO = _str_to_bool(DEFAULTS["DATABASE_ECHO"]) if "DATABASE_ECHO" in DEFAULTS else False

        self.MIDDLEWARES = _get_value("MIDDLEWARES", conversion_func=_to_list, default=DEFAULTS.get("MIDDLEWARES", []))
        if not isinstance(self.MIDDLEWARES, list): self.MIDDLEWARES = []

        self.ALLOWED_HOSTS = _get_value("ALLOWED_HOSTS", conversion_func=_to_list, default=DEFAULTS.get("ALLOWED_HOSTS", []))
        if not isinstance(self.ALLOWED_HOSTS, list): self.ALLOWED_HOSTS = []



        db_host = _get_value("DB_HOST", default=DEFAULTS["DB_HOST"])
        db_port = _get_value("DB_PORT", conversion_func=_to_int, default=DEFAULTS["DB_PORT"])
        db_user = _get_value("DB_USER", default=DEFAULTS["DB_USER"])
        db_password_encrypted_raw = _get_value("DB_PASSWORD_ENCRYPTED", default=DEFAULTS["DB_PASSWORD_ENCRYPTED"]) 
        db_name = _get_value("DB_NAME", default=DEFAULTS["DB_NAME"])

        self.DATABASE_URL = _get_value("DATABASE_URL", default=None) 


        self.DATABASE_CONFIG = {
            "engine": self.DB_ENGINE,
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": self.decrypt(db_password_encrypted_raw),
            "database": db_name
        }

        api_key_1_encrypted_raw = _get_value("API_KEY_SERVICE_1_ENCRYPTED", default=DEFAULTS["API_KEY_SERVICE_1_ENCRYPTED"])
        api_key_2_encrypted_raw = _get_value("API_KEY_SERVICE_2_ENCRYPTED", default=DEFAULTS["API_KEY_SERVICE_2_ENCRYPTED"])

        self.API_KEYS = {
            "service_1": self.decrypt(api_key_1_encrypted_raw), 
            "service_2": self.decrypt(api_key_2_encrypted_raw),
        }

        smtp_server = _get_value("SMTP_SERVER", default=DEFAULTS["SMTP_SERVER"])
        smtp_port = _get_value("SMTP_PORT", conversion_func=_to_int, default=DEFAULTS["SMTP_PORT"])
        email_username = _get_value("EMAIL_USERNAME", default=DEFAULTS["EMAIL_USERNAME"])
        email_password = _get_value("EMAIL_PASSWORD", default=DEFAULTS["EMAIL_PASSWORD"])
        use_tls = _get_value("USE_TLS", default=DEFAULTS["USE_TLS"])
        sender_name = _get_value("SENDER_NAME", default=DEFAULTS["SENDER_NAME"])
        sender_email = _get_value("SENDER_EMAIL", default=DEFAULTS["SENDER_EMAIL"])

        self.EMAIL_CONFIG = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": email_username,
            "password": email_password,
            "use_tls": use_tls,
            "sender_name": sender_name,
            "sender_email": sender_email
        }

        jwt_secret_key = _get_value("JWT_SECRET_KEY", default=DEFAULTS["JWT_SECRET_KEY"])
        
        self.JWT_SECRET = {
            "secret_key": jwt_secret_key,
        }

        logger.info("Config instance attributes loaded.")


    @property
    def DATABASE_URI(self):
        """Generates the database connection URI based on configured engine and credentials."""
        engine = self.DB_ENGINE
        host = self.DATABASE_CONFIG.get("host")
        port = self.DATABASE_CONFIG.get("port")
        user = self.DATABASE_CONFIG.get("user")
        password = self.DATABASE_CONFIG.get("password")
        name = self.DATABASE_CONFIG.get("database")
        sqlite_url = self.DATABASE_URL

        if engine == "postgresql":
            if not all([user, password, host, port, name]):
                 missing = []
                 if user is None: missing.append("DB_USER")
                 if password is None: missing.append("DB_PASSWORD_ENCRYPTED (decrypted password is None)")
                 if host is None: missing.append("DB_HOST")
                 if port is None: missing.append("DB_PORT")
                 if name is None: missing.append("DB_NAME")
                 raise ValueError(f"Missing database credentials for PostgreSQL: {', '.join(missing)}")

            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        elif engine == "mysql":
             if not all([user, password, host, port, name]):
                 missing = []
                 if user is None: missing.append("DB_USER")
                 if password is None: missing.append("DB_PASSWORD_ENCRYPTED (decrypted password is None)")
                 if host is None: missing.append("DB_HOST")
                 if port is None: missing.append("DB_PORT")
                 if name is None: missing.append("DB_NAME")
                 raise ValueError(f"Missing database credentials for MySQL: {', '.join(missing)}")
             return f"mysql://{user}:{password}@{host}:{port}/{name}"
        elif engine in ("sqlite", "sqlite3"):
            if sqlite_url:
                return sqlite_url
            else:
                if name is None or name == "":
                     logger.warning("DATABASE_URL and DB_NAME not set for SQLite. Using default filename 'db.db'.")
                     db_file = "db.db"
                else:
                     db_file = name
                return f"sqlite:///{db_file}"
        else:
            raise ValueError(f"Unsupported database engine: {engine}")


    @staticmethod
    def validate(config_instance):
        """Validates critical configuration settings of a Config instance."""
        if not config_instance.SECRET_KEY:
            raise ValueError("SECRET_KEY is required.")

        if config_instance.DB_ENGINE not in ("postgresql", "mysql", "sqlite", "sqlite3"):
             raise ValueError(f"Invalid DB_ENGINE '{config_instance.DB_ENGINE}'. Supported values are 'postgresql', 'mysql', 'sqlite', and 'sqlite3'.")

        if config_instance.DB_ENGINE in ("postgresql", "mysql"):
             required_keys_in_dict = ["host", "port", "user", "password", "database"]
             if not all(config_instance.DATABASE_CONFIG.get(key) is not None for key in required_keys_in_dict):
                  missing = [key for key in required_keys_in_dict if config_instance.DATABASE_CONFIG.get(key) is None]
                  if "password" in missing and config_instance.DATABASE_CONFIG.get("password") is None:
                       missing[missing.index("password")] = "DB_PASSWORD_ENCRYPTED (decrypted password is None)"

                  raise ValueError(f"For {config_instance.DB_ENGINE}, missing required database credentials: {', '.join(missing)}")

        elif config_instance.DB_ENGINE in ("sqlite", "sqlite3"):
            if not (config_instance.DATABASE_URL or config_instance.DATABASE_CONFIG.get("database")):
                 logger.warning("DATABASE_URL or DB_NAME not set for SQLite. Using default filename 'db.db'.")

        if config_instance.LOGGING_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid LOGGING_LEVEL '{config_instance.LOGGING_LEVEL}'.")


        if not config_instance.EMAIL_CONFIG.get("smtp_server"):
             raise ValueError("SMTP_SERVER is required for email configuration.")
        if not config_instance.EMAIL_CONFIG.get("username"):
             raise ValueError("EMAIL_USERNAME is required for email configuration.")
