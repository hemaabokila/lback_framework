import logging
import importlib
from typing import List, Callable, Dict, Any, Optional, Tuple
from http import HTTPStatus
from sqlalchemy.orm import Session
import inspect

from .signals import SignalDispatcher
from .router import Router, RouteNotFound, MethodNotAllowed
from .middleware_manager import MiddlewareManager
from .templates import TemplateRenderer
from .config import Config
from .types import Request
from .response import Response, JSONResponse

from lback.utils.admin_user_manager import AdminUserManager
from lback.utils.session_manager import SessionManager
from lback.utils.user_manager import UserManager


IncludedUrlPatterns = Tuple[List[Tuple], str]

logger = logging.getLogger(__name__)

class AppController:
    """
    Manages the application flow for each incoming request.
    Responsible for routing, executing middleware chains (request and response),
    dispatching the request to the appropriate view, and managing the database
    session lifecycle (creation, commit, rollback, removal) within the request context.
    Also handles loading application components like routes and admin registrations
    from installed apps during initialization.
    Integrates SignalDispatcher to emit events throughout the request lifecycle.
    """
    def __init__(
        self,
        middleware_manager: MiddlewareManager,
        router: Router,
        template_renderer: TemplateRenderer,
        config: Config,
        admin_user_manager: AdminUserManager,
        session_manager: SessionManager,
        user_manager: UserManager,
        available_dependencies_instances: Dict[str, Any],
        dispatcher: SignalDispatcher
    ):
        """
        Initializes the AppController with necessary core dependencies.
        These dependencies are typically singletons managed globally (e.g., in core/server.py).

        Args:
            middleware_manager: The MiddlewareManager instance responsible for executing middlewares.
            router: The Router instance responsible for matching requests to views.
            template_renderer: The TemplateRenderer instance for rendering templates.
            config: The application Config instance containing application settings.
            admin_user_manager: The AdminUserManager instance for admin user business logic.
            session_manager: The SessionManager instance for session data storage.
            user_manager: The UserManager instance for regular user business logic.
            available_dependencies_instances: A dictionary mapping dependency names (str)
                                              to their instances, which will be made available
                                              on the request context for middlewares and views.
            dispatcher: The SignalDispatcher instance for sending signals.
        """
        self.middleware_manager = middleware_manager
        self.router = router
        self.template_renderer = template_renderer
        self.config = config
        self.admin_user_manager = admin_user_manager
        self.session_manager = session_manager
        self.user_manager = user_manager
        self.available_dependencies = available_dependencies_instances
        self.dispatcher = dispatcher

        self.view_param_to_request_attr_map: Dict[str, str] = {}

        for dep_name in self.available_dependencies.keys():
            self.view_param_to_request_attr_map[dep_name] = dep_name

        self.view_param_to_request_attr_map['app_session'] = 'session' 
        self.view_param_to_request_attr_map['db_session'] = 'db_session'
        self.view_param_to_request_attr_map['current_user'] = 'user' 
        self.view_param_to_request_attr_map['csrf_token'] = 'csrf_token'
        self.view_param_to_request_attr_map['logger'] = 'logger' 
        self.view_param_to_request_attr_map['admin_registry'] = 'admin_registry'
        logger.debug(f"AppController: View parameter to request attribute map initialized: {self.view_param_to_request_attr_map}")
        self._load_app_components()

    def _load_app_components(self):
        """
        Loads application components by processing the main URL patterns from
        the ROOT_URLCONF setting. Handles standard route tuples and the specific
        structure returned by the custom 'include' function.
        """
        logger.info("Loading application components (loading main URLs with include support).")
        root_urlconf: Optional[str] = getattr(self.config, 'ROOT_URLCONF', None)
        if not root_urlconf:
            logger.error("ROOT_URLCONF setting is not defined in the configuration. Cannot load main URL patterns.")
            return

        logger.info(f"Loading main URL patterns from: {root_urlconf}")
        try:
            main_urls_module = importlib.import_module(root_urlconf)
            if not hasattr(main_urls_module, 'urlpatterns') or not isinstance(main_urls_module.urlpatterns, list):
                logger.warning(f"Module '{root_urlconf}' has no valid 'urlpatterns' list found for loading routes.")
                return
            logger.info(f"Processing urlpatterns from {root_urlconf}")

            def process_patterns_list(url_patterns_list: List[Any], current_prefix: str = ""):
                """
                Recursively processes a list of URL patterns, applying the current prefix.
                Handles standard route tuples and the specific structure returned by
                the custom 'include' function.
                """
                for item in url_patterns_list:
                    if hasattr(item, 'module_path') and hasattr(item, 'prefix'):
                        logger.debug(f"Recognized include structure: module='{item.module_path}', prefix='{item.prefix}'")
                        try:
                            included_module = importlib.import_module(item.module_path)
                            if not hasattr(included_module, 'urlpatterns') or not isinstance(included_module.urlpatterns, list):
                                logger.warning(f"Included module '{item.module_path}' has no valid 'urlpatterns' list found for processing.")
                                continue
                            include_prefix_part = item.prefix if item.prefix is not None else ""
                            new_prefix = current_prefix.rstrip('/') + '/' + include_prefix_part.lstrip('/')
                            if new_prefix and not new_prefix.endswith('/'):
                                new_prefix += '/'
                            logger.debug(f"Processing included patterns from '{item.module_path}' under combined prefix: {new_prefix}")
                            process_patterns_list(included_module.urlpatterns, new_prefix)
                        except ImportError:
                            logger.error(f"Could not import included URL module specified in include: '{item.module_path}'")
                        except Exception as e:
                            logger.exception(f"Error processing included URL module '{item.module_path}': {e}")

                    elif isinstance(item, tuple) and len(item) >= 2 and isinstance(item[0], str) and (callable(item[1]) or isinstance(item[1], type)):
                        route_pattern: str = item[0]
                        view_func: Callable = item[1]
                        methods: Optional[List[str]] = item[2] if len(item) > 2 else None
                        name: Optional[str] = item[3] if len(item) > 3 else None
                        requires_auth: bool = item[4] if len(item) > 4 else True

                        processed_current_prefix = current_prefix.rstrip('/') + '/' if current_prefix else ""
                        full_pattern = processed_current_prefix + route_pattern.lstrip('/')

                        if not isinstance(route_pattern, str) or (not callable(view_func) and not isinstance(view_func, type)):
                            logger.warning(f"Skipping malformed route definition (invalid pattern or view): {item} under prefix {current_prefix}")
                            continue
                        if methods is not None and (not isinstance(methods, list) or not all(isinstance(m, str) for m in methods)):
                            logger.warning(f"Skipping route {full_pattern}: 'methods' must be a list of strings or None. Found {methods}.")
                            methods = None

                        self.router.add_route(full_pattern, view_func, methods=methods, name=name, requires_auth=requires_auth)
                        logger.debug(f"Added route: {full_pattern} (Methods: {methods}, Name: {name}, Auth: {requires_auth})")
                    else:
                        logger.warning(f"Skipping unrecognized item format in urlpatterns: {item} under prefix {current_prefix}. Expected route tuple or recognized include structure.")

            process_patterns_list(main_urls_module.urlpatterns, "")

        except ImportError:
            logger.error(f"Could not import ROOT_URLCONF module: '{root_urlconf}'.")
        except Exception as e:
            logger.exception(f"Error loading or processing routes from ROOT_URLCONF '{root_urlconf}': {e}")
        logger.info("Admin registration loading from INSTALLED_APPS has been removed as requested.")
        logger.info("Component loading completed.")

    def handle_request(self, request: Request) -> Response:
        """
        Handles an incoming request by orchestrating the application flow.
        This includes:
        1. Setting core dependencies on the request context.
        2. Executing the request middleware chain.
        3. Resolving the route using the router (if not short-circuited by middleware).
        4. Dispatching the request to the appropriate view.
        5. Managing the database session (commit on success, rollback on exception).
        6. Executing the response middleware chain.
        7. Returning the final Response object.
        Emits signals at key points in the request lifecycle.
        
        Args:
            request: The incoming Request object. This object is mutable
                     and carries context, user, session, etc., throughout the pipeline.
        
        Returns:
            The final Response object to be sent back to the client.
        
        Raises:
            RouteNotFound: If no route matches the request path.
            MethodNotAllowed: If a route matches but the HTTP method is not allowed.
            Exception: For any unhandled exceptions occurring during the pipeline
                       (these should ideally be caught by a higher-level error handler).
        """
        logger.debug(f"AppController: Starting request processing for {request.method} {request.path}")
        
        self.dispatcher.send("request_started", sender=self, request=request)
        logger.debug("Signal 'request_started' sent.")
        
        for dep_name, dep_instance in self.available_dependencies.items():
            if dep_instance is not None:
                request.set_context(**{dep_name: dep_instance})

        db_session: Optional[Session] = None
        final_response: Optional[Response] = None
        
        try:
            logger.debug(f"AppController: Running request middlewares for {request.path}")
            response_from_middleware = self.middleware_manager.process_request(request)
            
            if response_from_middleware:
                logger.debug(f"AppController: Middleware returned a response (status={response_from_middleware.status_code}). Bypassing router and view execution.")
                final_response = response_from_middleware
            else:
                logger.debug(f"AppController: Request middleware chain complete. Proceeding to route resolution for {request.path}")
                view: Callable
                path_variables: Dict[str, Any]
                requires_auth: bool
                try:
                    view, path_variables, requires_auth = self.router.resolve(request.path, request.method)
                except (RouteNotFound, MethodNotAllowed) as e:
                    logger.debug(f"AppController: Route resolution failed: {type(e).__name__}. Handling with error handler.")
                    if request.error_handler:
                        if isinstance(e, RouteNotFound):
                            final_response = request.error_handler.handle_404(request)
                        elif isinstance(e, MethodNotAllowed):
                            final_response = request.error_handler.handle_405(request, e.allowed_methods if isinstance(e, MethodNotAllowed) else None)
                        else:
                            logger.error(f"AppController: Unexpected routing exception type: {type(e).__name__}")
                            final_response = request.error_handler.handle_exception(e, request)
                        raise e
                    else:
                        logger.critical("AppController: error_handler_instance is None for routing exception. Re-raising.")
                        raise e 
                
                request.route_requires_auth = requires_auth
                request.path_params = path_variables 
            
                logger.debug(f"AppController: Route resolved. View: {getattr(view, '__name__', str(view))}, Requires Auth: {requires_auth}. Raw Path Params: {path_variables}")
                self.dispatcher.send("route_matched", sender=self, request=request, view=view, path_variables=path_variables)
                logger.debug("Signal 'route_matched' sent.")
                logger.debug(f"AppController: Dispatching to view: {getattr(view, '__name__', str(view))}")
                self.dispatcher.send("pre_view_execution", sender=self, request=request, view=view, path_variables=path_variables)
                logger.debug("Signal 'pre_view_execution' sent.")
                
                try:
                    resolved_kwargs: Dict[str, Any] = {}
                    try:
                        view_params = inspect.signature(view).parameters
                    except ValueError:
                        logger.warning(f"AppController: Could not get signature for view {getattr(view, '__name__', str(view))}. Attempting to call with raw path_variables as fallback.")
                        response_from_view = view(request, **path_variables)
                        pass
                    
                    else:
                        for param_name, param in view_params.items():
                            if param_name == 'request':
                                
                                continue
                            if param_name in path_variables:
                                resolved_kwargs[param_name] = path_variables[param_name]
                                logger.debug(f"AppController: Matched view parameter '{param_name}' with path variable.")
                            
                            elif param_name in self.available_dependencies:
                                resolved_kwargs[param_name] = self.available_dependencies[param_name]
                                logger.debug(f"AppController: Matched view parameter '{param_name}' directly with available dependency.")
                            elif param_name in self.view_param_to_request_attr_map:
                                request_attr_name = self.view_param_to_request_attr_map[param_name]
                                if hasattr(request, request_attr_name):
                                    resolved_kwargs[param_name] = getattr(request, request_attr_name)
                                    logger.debug(f"AppController: Matched view parameter '{param_name}' to request attribute '{request_attr_name}'.")
                                else:
                                    if param.default == inspect.Parameter.empty:
                                        logger.error(f"AppController: Missing required parameter '{param_name}' (expected as request attribute '{request_attr_name}') for view '{getattr(view, '__name__', 'UnknownView')}'.")
                                        raise TypeError(f"Missing required parameter: {param_name}")
                    
                            elif param_name == 'model':
                                model_name_from_path = path_variables.get('model_name')
                                if model_name_from_path:
                                    admin_registry = request.admin_registry
                                    if admin_registry:
                                        model_class = admin_registry.get_model(model_name_from_path)
                                        if model_class:
                                            resolved_kwargs['model'] = model_class
                                            logger.debug(f"AppController: Resolved model '{model_name_from_path}' to class {getattr(model_class, '__name__', str(model_class))} for view parameter 'model'.")
                                        else:
                                            logger.warning(f"AppController: Model '{model_name_from_path}' from path for view parameter 'model' not found in AdminRegistry.")
                                            raise RouteNotFound(f"Model '{model_name_from_path}' not registered.")
                                    else:
                                        logger.critical("AppController: AdminRegistry dependency missing while resolving 'model' parameter for view.")
                                        raise RuntimeError("AdminRegistry dependency missing.")
                                else:
                                    logger.warning(f"AppController: View expects 'model' parameter, but 'model_name' path variable is missing for view '{getattr(view, '__name__', 'Unknown')}'.")
                                    raise RouteNotFound(f"Model name missing from path for view parameter 'model'.")

                            elif param.default == inspect.Parameter.empty and param_name not in resolved_kwargs:
                                logger.error(f"AppController: Missing required parameter '{param_name}' for view '{getattr(view, '__name__', 'UnknownView')}'.")
                                raise TypeError(f"Missing required parameter: {param_name}")
                    
                    db_session = request.get_context('db_session') 

                    if isinstance(view, type):
                        view_instance = view()
                        response_from_view = view_instance.dispatch(request, **resolved_kwargs)
                    else:
                        response_from_view = view(request, **resolved_kwargs)

                    if not isinstance(response_from_view, Response):
                        logger.error(f"AppController: View '{getattr(view, '__name__', str(view))}' returned unexpected type: {type(response_from_view)}. Expected Response.")
                        final_response = JSONResponse(data={"error": "Internal Server Error", "message": f"View returned invalid type: {type(response_from_view)}"}, status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value)
                    else:
                        final_response = response_from_view
                    
                    logger.debug(f"AppController: View execution complete. Initial response status: {getattr(final_response, 'status_code', 'N/A')}")
                    
                    self.dispatcher.send("post_view_execution", sender=self, request=request, response=final_response)
                    logger.debug("Signal 'post_view_execution' sent.")
                
                except Exception as e:
                    logger.exception(f"AppController: Unhandled exception during view execution or argument resolution for {getattr(view, '__name__', str(view))} on {request.method} {request.path}.")
                    if db_session:
                        self.dispatcher.send("db_session_rolled_back", sender=self, request=request, session=db_session, exception=e)
                        logger.debug("Signal 'db_session_rolled_back' sent due to view/arg resolution exception.")
                        try:
                            db_session.rollback()
                            logger.debug("AppController: Database session rolled back due to view/arg resolution exception.")
                        except Exception as rb_e:
                            logger.error(f"AppController: Error during rollback after view/arg resolution exception: {rb_e}", exc_info=True)
                    raise e

                if db_session and final_response and int(final_response.status_code) < 400:
                    try:
                        db_session.commit()
                        self.dispatcher.send("db_session_committed", sender=self, request=request, session=db_session)
                        logger.debug("Signal 'db_session_committed' sent.")
                        logger.debug("AppController: Database session committed successfully.")
                    except Exception as e:
                        logger.error(f"AppController: Error committing database session for {request.method} {request.path}: {e}", exc_info=True)
                        if db_session:
                            self.dispatcher.send("db_session_rolled_back", sender=self, request=request, session=db_session, exception=e)
                            logger.debug("Signal 'db_session_rolled_back' sent due to commit error.")
                            try:
                                db_session.rollback()
                                logger.debug("AppController: Database session rolled back due to commit error.")
                            except Exception as rb_e:
                                logger.error(f"AppController: Error during rollback after commit error: {rb_e}", exc_info=True)
                        raise e
 
        except (RouteNotFound, MethodNotAllowed) as e:
            logger.debug(f"AppController: Caught routing exception: {type(e).__name__}. Handling with error handler.")
            if request.error_handler:
                if isinstance(e, RouteNotFound):
                    final_response = request.error_handler.handle_404(request)
                elif isinstance(e, MethodNotAllowed):
                    final_response = request.error_handler.handle_405(request, e.allowed_methods if isinstance(e, MethodNotAllowed) else None)
                else:
                    logger.error(f"AppController: Unexpected routing exception type: {type(e).__name__}")
                    final_response = request.error_handler.handle_exception(e, request)
                logger.info(f"AppController: Error handler returned response with status {getattr(final_response, 'status_code', 'N/A')}.")
            else:
                logger.critical("AppController: error_handler_instance is None for routing exception.")
                status_code = e.status_code if hasattr(e, 'status_code') else HTTPStatus.INTERNAL_SERVER_ERROR.value
                status_phrase = HTTPStatus(status_code).phrase if status_code in HTTPStatus.__members__.values() else "Internal Server Error"
                status = f"{status_code} {status_phrase}"
                headers_list = [('Content-type', 'text/plain')]
                final_response = Response(body=f"{status_phrase}: {e}".encode('utf-8'), status_code=status_code, headers=dict(headers_list))
        
        except Exception as e:
            logger.exception(f"AppController: Unhandled exception during request processing pipeline for {request.method} {request.path}.")
            self.dispatcher.send("exception_caught", sender=self, request=request, exception=e)
            logger.debug("Signal 'exception_caught' sent.")
            
            if db_session:
                try:
                    if db_session.is_active:
                        self.dispatcher.send("db_session_rolled_back", sender=self, request=request, session=db_session, exception=e)
                        logger.debug("Signal 'db_session_rolled_back' sent due to pipeline exception.")
                        db_session.rollback()
                        logger.debug("AppController: Database session rolled back due to pipeline exception.")
                    else:
                        logger.debug("AppController: DB session is not active, no rollback needed.")
                except Exception as rb_e:
                    logger.error(f"AppController: Error during rollback after pipeline exception: {rb_e}", exc_info=True)
            
            if request.error_handler:
                final_response = request.error_handler.handle_exception(e, request)
                logger.info(f"AppController: Error handler returned response with status {getattr(final_response, 'status_code', 'N/A')}.")
            else:
                logger.critical("AppController: error_handler_instance is None for unhandled exception.")
                final_response = Response(body=b"Internal Server Error: Unhandled exception and Error Handler not available.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
        if not isinstance(final_response, Response):
            logger.error("AppController: final_response is not a Response object after handling. Generating default error response.")
            final_response = Response(body=b"Internal Server Error: Invalid response generated.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})
        
        final_response_after_middleware: Response = self.middleware_manager.process_response(request, final_response)
        logger.debug(f"AppController: Response processing complete for {request.method} {request.path}. Returning final response (status={final_response_after_middleware.status_code}).")
        self.dispatcher.send("request_finished", sender=self, request=request, response=final_response_after_middleware)
        logger.debug("Signal 'request_finished' sent.")
        return final_response_after_middleware
    
    def add_route(self, path: str, view: Callable, methods: Optional[List[str]] = None, name: Optional[str] = None, requires_auth: bool = True):
        logger.debug(f"AppController: Adding route {path} ({methods}) [auth: {requires_auth}] via add_route method.")
        self.router.add_route(path, view, methods=methods, name=name, requires_auth=requires_auth)
