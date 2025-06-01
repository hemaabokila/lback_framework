import importlib
import inspect
import logging
from typing import Optional, Any, Type, Dict

from .middleware_manager import MiddlewareManager
from .config import Config


logger = logging.getLogger(__name__)


def import_class(class_path: str) -> Type[Any]:
    """
    Dynamically imports a class from a string path representing its full location
    (e.g., 'my_app.middlewares.MyCustomMiddleware').

    Args:
        class_path: The full string path of the class.

    Returns:
        The imported class type.

    Raises:
        ImportError: If the module or class cannot be imported.
        TypeError: If the imported object is not a class.
    """
    try:
        module_name, class_name = class_path.rsplit('.', 1)
    except ValueError:
        raise ImportError(f"Invalid class path format: {class_path}. Must be in module.Class format.")

    try:
        module = importlib.import_module(module_name)
        logger.debug(f"Successfully imported module: {module_name}")
    except ImportError as e:
        raise ImportError(f"Could not import module {module_name} for class {class_name}: {e}")

    try:
        cls = getattr(module, class_name)
        if not isinstance(cls, type):
             raise TypeError(f"Object {class_name} in module {module_name} is not a class.")
        logger.debug(f"Successfully imported class: {class_name} from {module_name}")
        return cls
    except AttributeError:
        raise ImportError(f"Class {class_name} not found in module {module_name}.")
    except TypeError as e:
        raise e


def create_middleware(
    middleware_class: Type[Any],
    available_dependencies_instances: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Instantiates a middleware class, injecting dependencies based on its constructor signature,
    the provided available dependency instances, and parameters from config.

    Args:
        middleware_class: The middleware class (not instance) to instantiate.
        available_dependencies_instances: A dictionary mapping dependency names (str) to their instances.
        params: A dictionary of parameters to pass to the middleware's __init__, typically from config.

    Returns:
        An instance of the middleware_class.

    Raises:
        TypeError: If the middleware class requires a dependency or parameter that is
                   not available or cannot be matched.
        Exception: For other errors during inspection or instantiation.
    """
    logger.debug(f"Attempting to instantiate middleware class: {middleware_class.__name__}")
    try:
        init_signature = inspect.signature(middleware_class.__init__)
        init_params = init_signature.parameters

        args_to_pass: Dict[str, Any] = {}

        for param_name, param in init_params.items():
            if param_name == 'self':
                continue

            if param_name in available_dependencies_instances:
                dependency_instance = available_dependencies_instances[param_name]
                if dependency_instance is not None:
                    args_to_pass[param_name] = dependency_instance
                    logger.debug(f"Injected dependency '{param_name}' for {middleware_class.__name__}")
                elif param.default is inspect.Parameter.empty:
                    logger.error(f"Middleware '{middleware_class.__name__}' requires dependency '{param_name}', but the provided instance is None and the parameter has no default value.")
                    raise TypeError(f"Middleware '{middleware_class.__name__}' requires dependency '{param_name}' which is not available.")
                continue

            if params and param_name in params:
                args_to_pass[param_name] = params[param_name]
                logger.debug(f"Injected parameter '{param_name}' from config params for {middleware_class.__name__}")
                continue

            if param.default is inspect.Parameter.empty and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                 logger.error(f"Middleware '{middleware_class.__name__}' requires unknown positional or keyword parameter '{param_name}'. This parameter name is not available in provided dependencies or config params, and has no default.")
                 raise TypeError(f"Middleware '{middleware_class.__name__}' requires unknown parameter '{param_name}'.")

        instance = middleware_class(**args_to_pass)
        logger.debug(f"Successfully instantiated middleware: {middleware_class.__name__}")
        return instance

    except TypeError as te:
         logger.error(f"TypeError during instantiation of middleware {middleware_class.__name__}: {te}")
         raise te
    except Exception as e:
        logger.error(f"Unexpected error inspecting or instantiating middleware {middleware_class.__name__}: {e}", exc_info=True)
        raise


def load_middlewares_from_config(
    middleware_manager: MiddlewareManager,
    config: Config,
    available_dependencies_instances: Dict[str, Any]
):
    """
    Loads and registers middleware instances based on a list defined in the application configuration.
    Reads the middleware list from a Config object, imports classes, and instantiates them
    using the available dependencies and parameters from the config, adding them to MiddlewareManager in order.

    Args:
        middleware_manager: The MiddlewareManager instance to add middlewares to.
        config: The Config instance containing the middleware list (e.g., config.MIDDLEWARES).
        available_dependencies_instances: A dictionary mapping dependency names (str) to their instances.
    """
    middleware_list = getattr(config, 'MIDDLEWARES', None)

    if middleware_list is None:
        logger.warning("Setting 'MIDDLEWARES' not found in the config object. Skipping middleware loading.")
        return

    if not isinstance(middleware_list, list):
        logger.error(f"Setting 'MIDDLEWARES' in config must be a list, but found {type(middleware_list)}. Skipping middleware loading.")
        return

    if not middleware_list:
        logger.info("The 'MIDDLEWARES' list in config is empty. Skipping middleware loading.")
        return


    logger.info("Starting middleware loading from config...")

    loaded_middlewares_count = 0
    for index, middleware_item in enumerate(middleware_list):
        middleware_class_path = None
        middleware_params = None

        if isinstance(middleware_item, str):
            middleware_class_path = middleware_item
        elif isinstance(middleware_item, dict):
            middleware_class_path = middleware_item.get("class")
            middleware_params = middleware_item.get("params")
            if not isinstance(middleware_class_path, str):
                 logger.error(f"Middleware item at index {index} in config is a dictionary but is missing a 'class' string key or its value is not a string. Skipping item.")
                 continue
            if middleware_params is not None and not isinstance(middleware_params, dict):
                 logger.warning(f"Middleware item '{middleware_class_path}' at index {index} has a 'params' key, but its value is not a dictionary ({type(middleware_params)}). Parameters will be ignored.")
                 middleware_params = None

        else:
            logger.error(f"Middleware item at index {index} in config is not a string or dictionary ({type(middleware_item)}). Skipping item.")
            continue

        if not middleware_class_path:
             logger.error(f"Middleware item at index {index} in config is missing a class path. Skipping item.")
             continue

        try:
            middleware_class = import_class(middleware_class_path)
            try:
                 from .base_middleware import BaseMiddleware
                 is_valid_middleware = (
                     isinstance(middleware_class, type) and
                     issubclass(middleware_class, BaseMiddleware) and
                     middleware_class is not BaseMiddleware and
                     not inspect.isabstract(middleware_class)
                 )
            except ImportError:
                  is_valid_middleware = (
                       isinstance(middleware_class, type) and
                       hasattr(middleware_class, 'process_request') and callable(middleware_class.process_request) and
                       hasattr(middleware_class, 'process_response') and callable(middleware_class.process_response) and
                       (not inspect.isabstract(middleware_class) if isinstance(middleware_class, type) else False)
                  )

            if not is_valid_middleware:
                 logger.error(f"Imported object '{middleware_class_path}' is not a valid middleware class (does not inherit from BaseMiddleware or is abstract). Skipping item.")
                 continue

            logger.debug(f"Found middleware class: {middleware_class.__name__} for path {middleware_class_path}")
            try:
                instance = create_middleware(
                    middleware_class,
                    available_dependencies_instances=available_dependencies_instances,
                    params=middleware_params
                )
                middleware_manager.add_middleware(instance)
                logger.info(f"Successfully loaded and registered middleware: {middleware_class.__name__} ({middleware_class_path})")
                loaded_middlewares_count += 1

            except Exception as instantiation_error:
                logger.error(f"Failed to instantiate middleware {middleware_class.__name__} ({middleware_class_path}): {instantiation_error}", exc_info=True)

        except (ImportError, TypeError) as import_or_type_error:
            logger.error(f"Error importing or validating middleware class '{middleware_class_path}': {import_or_type_error}", exc_info=True)
        except Exception as e:
             logger.exception(f"An unexpected error occurred while processing middleware '{middleware_class_path}' from config: {e}")


    logger.info(f"Middleware loading from config completed. Total successfully loaded: {loaded_middlewares_count}")