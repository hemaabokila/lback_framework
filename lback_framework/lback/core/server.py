import logging
from http import HTTPStatus
from werkzeug.serving import run_simple
from typing import List, Callable, Any, Optional, Dict, Union
import importlib.util
import os
import sys
import time
from dotenv import load_dotenv

from .router import Router, RouteNotFound, MethodNotAllowed
from .middleware_manager import MiddlewareManager
from .response import Response
from .config_manager import get_project_root, start_settings_watcher
from .middleware_loader import load_middlewares_from_config
from .app_controller import AppController
from .templates import TemplateRenderer
from .config import Config, CONFIG_FILE

from .types import Request
from .logging_setup import setup_logging
from .error_handler import ErrorHandler
from .signals import SignalDispatcher
from .signals import dispatcher 
from lback.utils.session_manager import SessionManager
from lback.utils.admin_user_manager import AdminUserManager
from lback.utils.user_manager import UserManager
from lback.auth.jwt_auth import JWTAuth
from lback.models.database import DatabaseManager
from lback.utils.email_sender import EmailSender 
from lback.utils.validation import PasswordValidator

try:
    import lback.admin.registry as admin_registry_module
    if hasattr(admin_registry_module, 'admin'):
        admin = admin_registry_module.admin 
    else:
        admin = None
except ImportError:
    admin = None


config: Optional[Config] = None
template_renderer: Optional[TemplateRenderer] = None
router: Optional[Router] = None
middleware_manager: Optional[MiddlewareManager] = None
session_manager: Optional[SessionManager] = None
admin_user_manager: Optional[AdminUserManager] = None
user_manager: Optional[UserManager] = None
jwt_auth_utility: Optional[JWTAuth] = None
app_controller: Optional[AppController] = None
db_manager: Optional[DatabaseManager] = None
project_root: Optional[str] = None
error_handler_instance: Optional[ErrorHandler] = None
_core_components_initialized = False


logger = logging.getLogger(__name__)

def initialize_core_components() -> None:
    """
    Initializes all core framework components and sets module-level variables.
    This function should be called once before running the server or adding routes.
    Includes loading settings, installed apps, and initializing managers.
    """

    global config, template_renderer, router, middleware_manager, \
           session_manager, admin_user_manager, user_manager, jwt_auth_utility, \
           app_controller, db_manager, project_root, _core_components_initialized, \
           logger, dispatcher, error_handler_instance, admin

    if _core_components_initialized:
        logger.info("Core components already initialized. Skipping.")
        return

    logger.info("--- Starting Core Components Initialization ---")
    
    

    try:
        load_dotenv()
        logger.info(".env file loaded.")
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")

    try:
        project_root = get_project_root()
        logger.info(f"Project root found: {project_root}")
    except Exception as e:
        logger.critical(f"Failed to determine project root: {e}. Cannot proceed.")
        raise

    try:
        start_settings_watcher(project_root)
        config_file_path = os.path.join(project_root, CONFIG_FILE)
        config = Config(config_file=config_file_path)
        logger.info("Config initialized with project root config file.")
    except Exception as e:
        logger.critical(f"Failed to initialize Config: {e}. Cannot proceed.")
        raise

    try:
        setup_logging(config)
        logger = logging.getLogger(__name__)
        logger.info("Basic logging setup complete.")
    except Exception as e:
        logger.warning(f"Failed to perform basic logging setup: {e}")

  
    settings_file_name = 'settings.py'
    settings_file_path = os.path.join(project_root, settings_file_name)
    settings_module_name = 'project_settings'

    if not os.path.exists(settings_file_path):
        logger.warning(f"Settings file not found at '{settings_file_path}'. Skipping loading settings from file.")
    else:
        try:
            spec = importlib.util.spec_from_file_location(settings_module_name, settings_file_path)
            if spec is None:
                logger.error(f"Could not create module spec for settings file '{settings_file_path}'.")
            else:
                settings_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(settings_module)

                logger.info(f"Loading settings from settings file: {settings_file_path} into current config object.")
                loaded_settings_count = 0
                for setting_name in dir(settings_module):
                    if setting_name.isupper() and not setting_name.startswith('__'):
                        setting_value = getattr(settings_module, setting_name)
                        setattr(config, setting_name, setting_value)
                        loaded_settings_count += 1
                logger.info(f"Finished loading {loaded_settings_count} settings from {settings_file_path}")

                if not hasattr(config, 'ROOT_URLCONF') or not getattr(config, 'ROOT_URLCONF'):
                    logger.warning(f"ROOT_URLCONF setting was not found or is empty in {settings_file_path} after loading.")
                else:
                    logger.debug(f"ROOT_URLCONF found in config: {config.ROOT_URLCONF}")

        except Exception as e:
            logger.exception(f"An error occurred while loading settings from {settings_file_path}: {e}")


    try:
        setup_logging(config)
        logger = logging.getLogger(__name__)
        logger.info("Logging re-configured using application settings from config.")
    except Exception as e:
        logger.warning(f"Failed to perform application-level logging setup: {e}")

    try:
        Config.validate(config)
        logger.info("Configuration validated successfully.")
    except ValueError as e:
        logger.critical(f"Critical Configuration Error: {e}. Cannot proceed.")
        sys.exit(f"Critical Configuration Error: {e}")

    try:
        import lback.admin.registry as admin_registry_module 
        logger.info("Successfully imported lback.admin.registry (AdminRegistry defined).")
        if hasattr(admin_registry_module, 'admin'):
            admin = admin_registry_module.admin
            logger.info("Successfully obtained 'admin' instance from lback.admin.registry.")
        else:
            logger.critical("CRITICAL ERROR: Imported lback.admin.registry module does not have a global 'admin' instance.")
            admin = None
        import lback.admin.admin
        logger.info("Successfully imported lback.admin.admin (AdminUser registration attempted).")

    except ImportError as e:
        logger.critical(f"CRITICAL ERROR: Failed to import lback.admin.registry or lback.admin.admin: {e}. Admin functionality will be limited or unavailable.")
        admin = None
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: An unexpected error occurred during import of admin modules: {e}", exc_info=True)
        admin = None


    logger.info("Attempting to load installed apps and their admin modules.")
    if hasattr(config, 'INSTALLED_APPS') and isinstance(config.INSTALLED_APPS, (list, tuple)):
        for app_name in config.INSTALLED_APPS:
            if app_name == 'admin':
                logger.debug("Skipping built-in 'admin' app during installed apps loading.")
                continue

            admin_module_name = f"{app_name}.admin"
            try:
                importlib.import_module(admin_module_name)
                logger.info(f"Successfully imported admin module for app: '{app_name}' ({admin_module_name}).")
            except ModuleNotFoundError:
                logger.debug(f"No admin module found for app: '{app_name}' ({admin_module_name}). Skipping.")
            except Exception as e:
                logger.exception(f"Error importing admin module for app: '{app_name}' ({admin_module_name}): {e}")
    else:
        logger.warning("INSTALLED_APPS setting not found or is not a list/tuple in config. Skipping installed apps loading.")
    logger.info("Finished attempting to load installed apps and their admin modules.")
    
    email_sender = EmailSender(
        smtp_server=config.EMAIL_CONFIG['smtp_server'],
        smtp_port=config.EMAIL_CONFIG['smtp_port'],
        smtp_username=config.EMAIL_CONFIG['username'],   
        smtp_password=config.EMAIL_CONFIG['password'],
        sender_email=config.EMAIL_CONFIG['username'],
        sender_name=config.EMAIL_CONFIG['sender_name'],
        use_tls=True
    )

    logger.info("EmailSender initialized.")

    password_validator = PasswordValidator()
    logger.info("PasswordValidator initialized.")


    try:
        router = Router()
        middleware_manager = MiddlewareManager() 
        session_timeout = getattr(config, 'SESSION_TIMEOUT_MINUTES', 30)
        session_manager = SessionManager(timeout_minutes=session_timeout)
        admin_user_manager = AdminUserManager()
        user_manager = UserManager(email_sender=email_sender, password_validator=password_validator)

        jwt_config = getattr(config, 'JWT_SECRET', {})
        jwt_secret_key = jwt_config.get('secret_key')

        if not jwt_secret_key or not isinstance(jwt_secret_key, str):
            logger.critical("JWT_SECRET_KEY is not set or is not a string in configuration. JWT authentication will fail.")
            raise ValueError("JWT_SECRET_KEY (secret_key within JWT_SECRET) is required and must be a string in Config.")

        jwt_auth_utility = JWTAuth(secret=jwt_secret_key, algorithm="HS256")

        
        db_manager = DatabaseManager.get_instance()
        logger.info("DatabaseManager instance obtained.")
        template_renderer = TemplateRenderer(config=config)
        error_handler_instance = ErrorHandler(config=config, template_renderer=template_renderer, router=router)
        logger.info("ErrorHandler initialized.")

        if not isinstance(dispatcher, SignalDispatcher):
            dispatcher = SignalDispatcher()
            logger.info("SignalDispatcher initialized (replaced dummy).")
        else:
            logger.info("SignalDispatcher already initialized.")

        from lback.security.headers import SecurityHeadersConfigurator
        headers_configurator = SecurityHeadersConfigurator(config=config)
        logger.info("SecurityHeadersConfigurator initialized.")

        from lback.security.rate_limiter import RateLimiter
        rate_limiting_settings = getattr(config, 'RATE_LIMITING_SETTINGS', {})
        max_requests = rate_limiting_settings.get('MAX_REQUESTS', 100)
        window_seconds = rate_limiting_settings.get('WINDOW_SECONDS', 60)
        rate_limiter_instance = RateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        logger.info(f"RateLimiter initialized with max_requests={max_requests}, window_seconds={window_seconds}.")

        from lback.security.firewall import AdvancedFirewall
        firewall_settings = getattr(config, 'FIREWALL_SETTINGS', {})
        firewall_instance = AdvancedFirewall(
            allowed_ips=firewall_settings.get('ALLOWED_IPS'),
            blocked_ips=firewall_settings.get('BLOCKED_IPS'),
            blocked_networks=firewall_settings.get('BLOCKED_NETWORKS'),
            blocked_user_agents=firewall_settings.get('BLOCKED_USER_AGENTS'),
            blocked_url_patterns=firewall_settings.get('BLOCKED_URL_PATTERNS'),
            ddos_max_requests=firewall_settings.get('DDOS_MAX_REQUESTS', 100),
            ddos_window_seconds=firewall_settings.get('DDOS_WINDOW_SECONDS', 10),
            temp_block_seconds=firewall_settings.get('TEMP_BLOCK_SECONDS', 300),
        )
        logger.info("AdvancedFirewall initialized.")

        available_dependencies_instances = {
            'session_manager': session_manager,
            'admin_user_manager': admin_user_manager,
            'user_manager': user_manager,
            'config': config,
            'jwt_auth': jwt_auth_utility,
            'db_manager': db_manager,
            'logger': logger,
            'template_renderer': template_renderer,
            'router': router,
            'error_handler': error_handler_instance,
            'dispatcher': dispatcher,
            'firewall': firewall_instance,
            'headers_configurator': headers_configurator,
            'rate_limiter': rate_limiter_instance,
            'admin_registry': admin
        }
        logger.info("Core framework components initialized and dependencies dictionary created.")

    except Exception as e:
        logger.critical(f"Failed to initialize core components: {e}. Cannot proceed.", exc_info=True)
        sys.exit(f"Failed to initialize core components: {e}")

    try:
        load_middlewares_from_config(middleware_manager, config, available_dependencies_instances=available_dependencies_instances)
        logger.info("Middlewares loaded and configured.")
    except Exception as e:
        logger.critical(f"Failed to load and configure middlewares: {e}. Cannot proceed.", exc_info=True)
        sys.exit(f"Failed to load and configure middlewares: {e}")

    try:
        logger.info("Initializing AppController...")
        app_controller = AppController(
            middleware_manager=middleware_manager,
            router=router,
            template_renderer=template_renderer,
            config=config,
            admin_user_manager=admin_user_manager,
            session_manager=session_manager,
            user_manager=user_manager,
            available_dependencies_instances=available_dependencies_instances,
            dispatcher=dispatcher,
        )
        logger.info("AppController initialized successfully.")
        logger.info("--- Core Components Initialization Complete ---")

        _core_components_initialized = True

    except Exception as e:
        logger.critical(f"Failed to initialize AppController: {e}. Cannot proceed.", exc_info=True)
        sys.exit(f"Failed to initialize AppController: {e}")


def wsgi_application(environ: Dict[str, Any], start_response: Callable) -> Any:
    """
    WSGI application entry point for handling incoming requests.
    Parses WSGI environment, creates a Request object, delegates to AppController,
    handles errors, and returns a WSGI-compatible response.
    Accesses core components from module-level variables (initialized by initialize_core_components).
    CORRECTED: Defers body reading for methods handled by BodyParsingMiddleware
               to prevent premature stream exhaustion.
    """

    if any(comp is None for comp in [config, app_controller, error_handler_instance, project_root, dispatcher,
                                     db_manager, admin_user_manager, session_manager, user_manager,
                                     jwt_auth_utility, admin if 'admin' in globals() else None]):
         logger.critical("CRITICAL ERROR: Core framework components are not initialized. Cannot handle WSGI request.")
         status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
         headers_list = [('Content-type', 'text/plain')]
         start_response(status, headers_list)
         try:
             if dispatcher:
                 dispatcher.send("wsgi_application_error", sender="wsgi_application", error_type="core_components_not_initialized", environ=environ)
             else:
                 logging.warning("Dispatcher is None. Cannot send 'wsgi_application_error' signal.")
         except Exception as e_sig: logging.error(f"Error emitting signal: {e_sig}", exc_info=True)
         return [b"Internal Server Error: Framework not initialized."]

    start_time = time.time()
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    query_string = environ.get('QUERY_STRING', '')
    raw_path_with_query = f"{path}{'?' + query_string if query_string else ''}"

    logger.info(f"[{method}] >>> Start handling WSGI request for path: {raw_path_with_query}")

    try:
        headers = {k.replace('HTTP_', '').replace('_', '-').upper(): v for k, v in environ.items() if k.startswith('HTTP_')}
        if 'CONTENT_TYPE' in environ:
             headers['CONTENT-TYPE'] = environ['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in environ:
             headers['CONTENT-LENGTH'] = environ['CONTENT_LENGTH']

        if dispatcher:
             dispatcher.send("server_request_received", sender="wsgi_application", method=method, path=path, full_path=raw_path_with_query, headers=headers, environ=environ)
             logging.debug(f"Signal 'server_request_received' sent for {method} {raw_path_with_query}.")
        else:
             logging.warning("Dispatcher is None. Cannot send 'server_request_received' signal.")
    except Exception as e:
        logging.error(f"Error emitting 'server_request_received' signal: {e}", exc_info=True)

    response: Optional[Response] = None
    request: Optional[Request] = None

    content_length_str = environ.get('CONTENT_LENGTH')
    content_length = 0

    if content_length_str is not None and content_length_str.isdigit():
        try:
            content_length = int(content_length_str)
        except ValueError:
            logger.warning(f"[{method}] Could not convert CONTENT_LENGTH '{content_length_str}' to int for path: {raw_path_with_query}. Treating as 0.")
            content_length = 0
    elif content_length_str is not None and not content_length_str.isdigit():
        logger.warning(f"[{method}] Received invalid CONTENT_LENGTH '{content_length_str}' for path: {raw_path_with_query}. Treating as 0.")
        content_length = 0

    body: Union[str, bytes, None] = None 

    max_body_size = getattr(config, 'MAX_REQUEST_BODY_SIZE', 10 * 1024 * 1024)
    if content_length > max_body_size:
         logger.warning(f"[{method}] Request body too large ({content_length} bytes) for path: {raw_path_with_query}. Max allowed: {max_body_size} bytes.")
         if error_handler_instance is None:
                logger.critical("WSGI Application: error_handler_instance is None for 413 (Payload Too Large).")
                status = f"{HTTPStatus.REQUEST_ENTITY_TOO_LARGE.value} {HTTPStatus.REQUEST_ENTITY_TOO_LARGE.phrase}"
                headers_list = [('Content-type', 'text/plain')]
                start_response(status, headers_list)
                return [b"Payload Too Large: Error handler not initialized."]
         try:
             dummy_request = Request(raw_path_with_query, method, b'', headers, environ=environ)
         except Exception as req_e:
              logger.critical(f"[{method}] Failed to create dummy Request object for 413 error handling: {req_e}", exc_info=True)
              status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
              headers_list = [('Content-type', 'text/plain')]
              start_response(status, headers_list)
              return [b"Internal Server Error: Failed to create request object for error handling."]
         
         response = error_handler_instance.handle_custom_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE.value, "Request body too large.", request=dummy_request)
         logger.debug("WSGI Application: Handled 413 Request body too large.")

    if response is None:
         try:
             request = Request(raw_path_with_query, method, body, headers, environ=environ)
             logger.debug("WSGI Application: Main Request object created.")
         except Exception as req_e:
             logger.critical(f"[{method}] Failed to create main Request object for path: {raw_path_with_query}: {req_e}", exc_info=True)
             if error_handler_instance is None:
                logger.critical("WSGI Application: error_handler_instance is None after critical Request creation error.")
                status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                headers_list = [('Content-type', 'text/plain')]
                start_response(status, headers_list)
                return [b"Internal Server Error: Failed to create request object."]

             try:
                 dummy_request_for_error = Request(raw_path_with_query, method, b'', headers, environ=environ)
             except Exception as final_req_e:
                  logger.critical(f"WSGI Application: Failed to create final error request object: {final_req_e}", exc_info=True)
                  status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                  headers_list = [('Content-type', 'text/plain')]
                  start_response(status, headers_list)
                  return [b"Internal Server Error: Unrecoverable error creating request object."]
             
             response = error_handler_instance.handle_exception(req_e, request=dummy_request_for_error)

    if request is not None and response is None:
         try:

             if not hasattr(request, 'add_context') or not callable(request.add_context):
                  logger.critical("WSGI Application: Request object does not have an add_context method.")
                  raise RuntimeError("Request add_context method is missing. Ensure lback.core.types.Request is correctly updated.")

             if db_manager is None:
                  logger.critical("WSGI Application: db_manager is None during request processing.")
                  raise RuntimeError("Database Manager not initialized.")

             if not hasattr(db_manager, 'get_instance') or not callable(db_manager.get_instance):
                  logger.critical("WSGI Application: db_manager does not have a get_instance method.")
                  raise RuntimeError("Database Manager get_instance method is missing.")

             db_session = db_manager.get_instance()
             request.add_context('db_session', db_session)
             logger.debug("WSGI Application: Added DB session to request context.")

             if config: request.add_context('config', config)
             if template_renderer: request.add_context('template_renderer', template_renderer)
             if router: request.add_context('router', router)
             if admin_user_manager: request.add_context('admin_user_manager', admin_user_manager)
             if session_manager: request.add_context('session_manager', session_manager)
             if user_manager: request.add_context('user_manager', user_manager)
             if jwt_auth_utility: request.add_context('jwt_auth_utility', jwt_auth_utility)
             if error_handler_instance: request.add_context('error_handler', error_handler_instance)
             if dispatcher: request.add_context('dispatcher', dispatcher)
             if 'admin' in globals() and admin:
                  request.add_context('admin_registry', admin)
             if environ: request.add_context('environ', environ)

             logger.debug("WSGI Application: Added dependencies to request context.")

         except Exception as e:
             logger.critical(f"WSGI Application: Error adding dependencies to request context: {e}", exc_info=True)
             if error_handler_instance is None:
                 logger.critical("WSGI Application: error_handler_instance is None after dependency injection error.")

                 status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                 headers_list = [('Content-type', 'text/plain')]
                 start_response(status, headers_list)

                 if request:
                     db_session_from_context = request.get_context('db_session')
                     if db_session_from_context and hasattr(db_session_from_context, 'close') and callable(db_session_from_context.close):
                          try:
                               db_session_from_context.close()
                               logger.debug("WSGI Application: Closed DB session after DI error (request exists).")
                          except Exception as close_e:
                               logger.error(f"WSGI Application: Error closing DB session after DI error: {close_e}")
                 return [b"Internal Server Error: Could not prepare request context."]

             try:
                 dummy_request_for_error = Request(raw_path_with_query, method, b'', headers, environ=environ)
             except Exception as final_req_e:
                  logger.critical(f"WSGI Application: Failed to create error request object after DI error: {final_req_e}", exc_info=True)
                  status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                  headers_list = [('Content-type', 'text/plain')]
                  start_response(status, headers_list)
                  return [b"Internal Server Error: Unrecoverable error creating request object for error handling after DI error."]
             response = error_handler_instance.handle_exception(e, request=dummy_request_for_error)

    final_response: Optional[Response] = None

    if response is None:
         try:
             if app_controller is None:
                  logger.critical("WSGI Application: app_controller is None before handling request.")
                  raise RuntimeError("AppController not initialized.")

             final_response = app_controller.handle_request(request)
             logger.debug(f"WSGI Application: AppController returned response with status {getattr(final_response, 'status_code', 'N/A')}.")
         except RouteNotFound:
             logger.warning(f"[{method}] Route not found for {raw_path_with_query}")

             if error_handler_instance is None: 
                  logger.critical("WSGI Application: error_handler_instance is None for 404.")
                  status = f"{HTTPStatus.NOT_FOUND.value} {HTTPStatus.NOT_FOUND.phrase}"
                  headers_list = [('Content-type', 'text/plain')]
                  start_response(status, headers_list)
                  return [b"Not Found: Error handler not initialized."]

             final_response = error_handler_instance.handle_404(request)
             logger.info(f"[{method}] <<< Finished handling request (404 Not Found) for path: {raw_path_with_query}")

         except MethodNotAllowed as e:
             logger.warning(f"[{method}] Method not allowed for {raw_path_with_query}. Allowed: {', '.join(e.allowed_methods)}")

             if error_handler_instance is None:
                  logger.critical("WSGI Application: error_handler_instance is None for 405.")

                  status = f"{HTTPStatus.METHOD_NOT_ALLOWED.value} {HTTPStatus.METHOD_NOT_ALLOWED.phrase}"
                  headers_list = [('Content-type', 'text/plain')]
                  start_response(status, headers_list)
                  return [b"Method Not Allowed: Error handler not initialized."]

             final_response = error_handler_instance.handle_405(request, e.allowed_methods)
             logger.info(f"[{method}] <<< Finished handling request (405 Method Not Allowed) for path: {raw_path_with_query}")

         except Exception as e:
             logger.exception(f"[{method}] Unhandled exception during request processing for {raw_path_with_query}.")

             if error_handler_instance is None:
                  logger.critical("WSGI Application: error_handler_instance is None for unhandled exception.")
                  status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                  headers_list = [('Content-type', 'text/plain')]
                  start_response(status, headers_list)
                  return [b"Internal Server Error: Error handler not initialized."]
             final_response = error_handler_instance.handle_exception(e, request)
             logger.info(f"[{method}] <<< Finished handling request (Unhandled Exception) for path: {raw_path_with_query}")
    else:
         final_response = response
         logger.debug(f"WSGI Application: Using pre-generated error response with status {getattr(final_response, 'status_code', 'N/A')}.")

    try:
        end_time = time.time()
        duration = end_time - start_time 
        if request:
            db_session_from_context = request.get_context('db_session')
            if db_session_from_context and hasattr(db_session_from_context, 'close') and callable(db_session_from_context.close):
                 try:
                      db_session_from_context.close()
                      logger.debug("WSGI Application: Database session closed in finally block.")
                 except Exception as e:
                      logger.error(f"WSGI Application: Error closing database session in finally block: {e}", exc_info=True)
            elif request.get_context('db_session') is not None:
                 logger.warning(f"WSGI Application: DB session object in context ({type(request.get_context('db_session'))}) does not have a close method in finally.")
        else:
            logger.warning("WSGI Application: Request object was not created. Cannot close DB session in finally block.")

        if dispatcher:
            final_status = getattr(final_response, 'status_code', 'N/A') if final_response else 'N/A'
            dispatcher.send("server_request_finished", sender="wsgi_application", method=method, path=path, full_path=raw_path_with_query, duration=duration, status_code=final_status, response=final_response, request=request)
            logging.debug(f"Signal 'server_request_finished' sent for {method} {raw_path_with_query}. Duration: {duration:.4f}s, Status: {final_status}.")
        else:
            logging.warning("Dispatcher is None. Cannot send 'server_request_finished' signal.")

    except Exception as e:
        logging.critical(f"WSGI Application: CRITICAL error in finally block: {e}", exc_info=True)

        status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
        headers_list = [('Content-type', 'text/plain')]
        start_response(status, headers_list)
        return [b"Internal Server Error: CRITICAL error during response finalization."]
    
    if final_response is None:
         logger.critical("WSGI Application: final_response is None after all processing. Returning a default 500 error.")
         if request is None:
              try:
                  request = Request(raw_path_with_query, method, b'', headers, environ=environ) 
              except Exception as req_e:
                   logger.critical(f"[{method}] Failed to create Request object for final 500 handling: {req_e}", exc_info=True)
                   if error_handler_instance is None:
                       logger.critical("WSGI Application: error_handler_instance is None for final 500.")
                       status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                       headers_list = [('Content-type', 'text/plain')]
                       start_response(status, headers_list)
                       return [b"Internal Server Error: Error handler not initialized."]
                   final_response = error_handler_instance.handle_custom_error(HTTPStatus.INTERNAL_SERVER_ERROR.value, "Internal Server Error: No response generated.", request=None)
              else:
                   if error_handler_instance is None:
                       logger.critical("WSGI Application: error_handler_instance is None for final 500 (with request).")
                       status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                       headers_list = [('Content-type', 'text/plain')]
                       start_response(status, headers_list)
                       return [b"Internal Server Error: Error handler not initialized."]

                   final_response = error_handler_instance.handle_exception(RuntimeError("No response generated by application."), request=request)
         else:
              if error_handler_instance is None:
                  logger.critical("WSGI Application: error_handler_instance is None for final 500 (with request).")
                  status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
                  headers_list = [('Content-type', 'text/plain')]
                  start_response(status, headers_list)
                  return [b"Internal Server Error: Error handler not initialized."]

              final_response = error_handler_instance.handle_exception(RuntimeError("No response generated by application."), request=request)

    if not hasattr(final_response, 'get_wsgi_response') or not callable(final_response.get_wsgi_response):
         logger.critical(f"WSGI Application: Final response object does not have a get_wsgi_response method. Type: {type(final_response)}")
         status = f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}"
         headers_list = [('Content-type', 'text/plain')]
         start_response(status, headers_list)
         return [b"Internal Server Error: Invalid response object generated."]

    status_line, header_list_tuples, body_iterable = final_response.get_wsgi_response()
    start_response(status_line, header_list_tuples)

    logger.debug(f"--- END WSGI APPLICATION REQUEST PROCESSING --- Method: {method}, Path: {path}, Status: {status_line}")
    return body_iterable


class Server:
    """The main server class to set up and run the application."""
    def __init__(self):
        if not _core_components_initialized:
             initialize_core_components()
             logger.info("Server() constructor triggered core components initialization.")

    def add_route(self, path: str, view: Callable, methods: List[str] = ['GET'], name: str = None, requires_auth: bool = True) -> None:
        """Adds a route to the application router via the AppController."""
        # global app_controller
        if app_controller is None:
            raise RuntimeError("AppController not initialized. Cannot add route.")
        app_controller.add_route(path, view, methods=methods, name=name, requires_auth=requires_auth)

    def run(self, host, port) -> None:
        """Starts the WSGI development server."""

        if not _core_components_initialized or any(comp is None for comp in [config, project_root, app_controller, error_handler_instance, dispatcher, logger]):
             logger.critical("Core server components not initialized before calling Server().run(). Calling initialize_core_components() now.")
             initialize_core_components()
             if not _core_components_initialized or any(comp is None for comp in [config, project_root, app_controller, error_handler_instance, dispatcher, logger]):
                  raise RuntimeError("Failed to initialize core server components.")


        # threading.Thread(target=start_settings_watcher, args=(project_root,), daemon=True).start()
        # logger.info("Settings watcher thread started.")

        

        logger.info(f"WSGI Development Server is running on http://{host}:{port}...")

        try:
            run_simple(
                hostname=host,
                port=port,
                application=wsgi_application,
                use_reloader=True,
                use_debugger=True,
            )
        except KeyboardInterrupt:
            logger.info("Server stopped by user (KeyboardInterrupt caught).")
        finally:
            logger.info("Server shutting down.")

