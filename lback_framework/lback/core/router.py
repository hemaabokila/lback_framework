import logging
import re
from typing import Any, Dict, List, Tuple, Callable, Optional


from .exceptions import RouteNotFound, MethodNotAllowed


logger = logging.getLogger(__name__)

class Route:
    """
    Represents a single registered route in the routing system.
    Stores the path pattern, view callable, allowed methods, optional name,
    and whether the route requires authentication.
    """
    def __init__(self, path: str, view: Callable, methods: Optional[List[str]] = None, name: Optional[str] = None, requires_auth: bool = True):
        """
        Initializes a Route object.

        Args:
            path: The URL path pattern (e.g., '/users/{user_id:int}').
            view: The view function or class that will handle matching requests.
            methods: A list of allowed HTTP methods (e.g., ['GET', 'POST']). If None, all methods are allowed.
            name: An optional name for the route (useful for URL reversal).
            requires_auth: Boolean indicating if this route requires user authentication. Defaults to True.
        """
        if not isinstance(path, str) or not path.startswith('/'):
            logger.error(f"Invalid route path format: {path}. Must be a string starting with '/'.")
            raise ValueError(f"Invalid route path format: {path}")
        if not callable(view):
             logger.error(f"Invalid view provided for path '{path}'. Must be callable.")
             raise TypeError(f"Invalid view provided for path '{path}'. Must be callable.")
        if methods is not None and not isinstance(methods, list):
             logger.error(f"Invalid methods format for path '{path}'. Must be a list or None.")
             raise TypeError(f"Invalid methods format for path '{path}'. Must be a list or None.")
        if name is not None and not isinstance(name, str):
             logger.error(f"Invalid name format for path '{path}'. Must be a string or None.")
             raise TypeError(f"Invalid name format for path '{path}'. Must be a string or None.")
        if not isinstance(requires_auth, bool):
             logger.error(f"Invalid requires_auth format for path '{path}'. Must be a boolean.")
             raise TypeError(f"Invalid requires_auth format for path '{path}'. Must be a boolean.")


        self.path: str = path
        self.view: Callable = view
        self.methods: Optional[List[str]] = [m.upper() for m in methods] if methods is not None else None
        self.name: Optional[str] = name
        self.requires_auth: bool = requires_auth
        try:
            self._path_regex: str
            self._variable_names: List[str]
            self._path_regex, self._variable_names = self._build_path_regex(path)
            logger.debug(f"Route created: path='{self.path}', methods={self.methods}, regex='{self._path_regex}', variables={self._variable_names}, requires_auth={self.requires_auth}")
        except ValueError as e:
             logger.error(f"Error building regex for path '{path}': {e}")
             raise 


    def _build_path_regex(self, path: str) -> Tuple[str, List[str]]:
        """
        Builds the regex pattern for a path with dynamic variables.
        Handles variable definitions like '{variable_name}' or '{variable_name:type}'.
        Type hints are currently ignored in regex building but can be used later for type conversion.

        Args:
            path: The URL path pattern string.

        Returns:
            A tuple containing:
            - The regex pattern string for matching the path.
            - A list of variable names found in the path pattern.

        Raises:
            ValueError: If the path pattern contains malformed variable definitions.
        """
        variable_names: List[str] = []
        regex_parts: List[str] = []
        parts = re.split(r'(\{.*?\})', path)
        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                var_definition = part[1:-1]
                if ':' in var_definition:
                    var_name, var_type_str = var_definition.split(':', 1)
                else:
                    var_name = var_definition
                    var_type_str = None

                if not var_name:
                    logger.error(f"Empty variable name found in path: {path}")
                    raise ValueError(f"Empty variable name found in path: {path}")

                variable_names.append(var_name)
                regex_parts.append(rf'(?P<{var_name}>[^/]+)')
            else:
                regex_parts.append(re.escape(part))

        regex_pattern = '^' + ''.join(regex_parts) + '$'
        return regex_pattern, variable_names

    def match(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Checks if the route's path pattern matches the given path and if the method is allowed.

        Args:
            path: The incoming request path string.
            method: The incoming request HTTP method string (e.g., 'GET', 'POST').

        Returns:
            A dictionary of path variables if the path and method match.
            Returns a dictionary {'_method_mismatch': True, '_allowed_methods': [...]}
            if the path matches but the method is not allowed.
            Returns None if the path does not match the route's pattern.
        """

        match = re.match(self._path_regex, path)
        if not match:
            logger.debug(f"Path '{path}' did not match regex pattern for route '{self.path}'.")
            return None
        path_variables: Dict[str, str] = match.groupdict()

        if self.methods is not None and str(method) not in self.methods:
            logger.debug(f"Method '{method}' is not allowed for route '{self.path}'. Allowed methods: {self.methods}")
            return {'_method_mismatch': True, '_allowed_methods': self.methods}

        logger.debug(f"Found matching route: '{self.path}' for method {method} and path '{path}'. Extracted variables: {path_variables}")
        return path_variables


class Router:
    """
    Manages a collection of Route objects and provides methods for matching
    incoming requests to registered routes and generating URLs.
    """
    def __init__(self):
        """Initializes the Router with an empty list of routes."""
        self.routes: List[Route] = []
        logger.info("Router initialized.")

    def add_route(self, path: str, view: Callable, methods: Optional[List[str]] = None, name: Optional[str] = None, requires_auth: bool = True):
        """
        Adds a new route definition to the router.

        Args:
            path: The URL path pattern string.
            view: The view function or class to handle requests matching the pattern.
            methods: A list of HTTP methods allowed for this route (e.g., ['GET', 'POST']).
                     If None, attempts to get methods from a 'methods' attribute on the view callable.
                     If still None, all methods are allowed.
            name: An optional name for the route (useful for URL reversal).
            requires_auth: Boolean indicating if this route requires user authentication. Defaults to True.
        """
        if methods is None and hasattr(view, 'methods') and isinstance(getattr(view, 'methods'), list):
             methods = getattr(view, 'methods')
             logger.debug(f"Using methods from view callable '{getattr(view, '__name__', str(view))}': {methods}")

        try:
            route = Route(path, view, methods, name, requires_auth=requires_auth)
            self.routes.append(route) 
            logger.info(f"Route added: path='{path}', methods={methods}, view='{getattr(view, '__name__', str(view))}', requires_auth={requires_auth}")
        except (ValueError, TypeError) as e:
             logger.error(f"Failed to add route for path '{path}': {e}")
             raise


    def resolve(self, path: str, method: str) -> Tuple[Callable, Dict[str, Any], bool]:
        """
        Finds a matching route for the given path and method.

        Iterates through registered routes and uses the Route.match method.
        If a path matches but the method is not allowed, it collects allowed methods.

        Args:
            path: The incoming request path string.
            method: The incoming request HTTP method string.

        Returns:
            A tuple containing:
            - The view callable for the matched route.
            - A dictionary of extracted path variables.
            - A boolean indicating if the route requires authentication.

        Raises:
            RouteNotFound: If no route matches the path.
            MethodNotAllowed: If a route matches the path but not the method.
        """
        logger.debug(f"Attempting to resolve route: path='{path}' with method: '{method}'")
        matched_route: Optional[Route] = None
        path_variables: Dict[str, Any] = {}
        allowed_methods_for_path: List[str] = []

        for route in self.routes:
            match_result = route.match(path, method)

            if match_result is not None:
                if '_method_mismatch' in match_result:
                    if '_allowed_methods' in match_result and isinstance(match_result['_allowed_methods'], list):
                         for m in match_result['_allowed_methods']:
                             if m not in allowed_methods_for_path:
                                 allowed_methods_for_path.append(m)
                    logger.debug(f"Path matched for route '{route.path}', but method '{method}' is not allowed. Allowed: {route.methods}")
                else:
                    matched_route = route
                    path_variables = match_result
                    logger.debug(f"Full match found: route='{route.path}' for method {method} and path '{path}'. Extracted variables: {path_variables}")
                    break

        if matched_route is None:
            if allowed_methods_for_path:
                unique_allowed_methods = sorted(list(set(allowed_methods_for_path)))
                logger.warning(f"MethodNotAllowed: Method {method} not allowed for path {path}. Allowed: {', '.join(unique_allowed_methods)}")
                raise MethodNotAllowed(path=path, method=method, allowed_methods=unique_allowed_methods)
            else:
                logger.warning(f"RouteNotFound: No route found for method {method} and path {path}")
                raise RouteNotFound(path=path, method=method)

        logger.debug(f"Route resolved: '{matched_route.path}'. View: {getattr(matched_route.view, '__name__', str(matched_route.view))}, Requires Auth: {matched_route.requires_auth}")
        return matched_route.view, path_variables, matched_route.requires_auth


    def url_for(self, name: str, **params: Any) -> str:
        """
        Generates a URL for a route based on its name and provided parameters.

        Args:
            name: The name of the route.
            **params: Keyword arguments for the path variables in the route pattern.

        Returns:
            The generated URL string.

        Raises:
            ValueError: If no route with the given name is found or if required
                        parameters are missing for the route pattern.
        """
        logger.debug(f"Attempting to generate URL for route name: '{name}' with params: {params}")
        for route in self.routes:
            if route.name == name:
                try:
                    formatted_path = route.path
                    for param, value in params.items():
                        formatted_path = formatted_path.replace(f"{{{param}}}", str(value))

                    if '{' in formatted_path or '}' in formatted_path:
                        expected_params_missing = [
                             var_name for var_name in route._variable_names
                             if f"{{{var_name}}}" in formatted_path or f"{var_name}:" in formatted_path
                        ]
                        if expected_params_missing:
                            logger.error(f"Missing parameters for url_for('{name}'): {', '.join(expected_params_missing)}")
                            raise ValueError(f"Missing parameters for url_for('{name}'): {', '.join(expected_params_missing)}")
                        logger.warning(f"url_for('{name}'): Remaining curly braces in generated path '{formatted_path}'. Pattern issue or unexpected format?")


                    logger.debug(f"Successfully generated URL for '{name}': {formatted_path}")
                    return formatted_path
                except Exception as e:
                    logger.exception(f"Error formatting URL for route '{name}' with params {params}.")
                    raise ValueError(f"Error formatting URL for route '{name}': {e}")

        logger.warning(f"Route name not found: '{name}'.")
        raise ValueError(f"No route found with the name '{name}'.")


    def get_route_by_name(self, name: str) -> Optional[Route]:
        """
        Retrieves a Route object based on its name.

        Args:
            name: The name of the route to find.

        Returns:
            The Route object if found, otherwise None.
        """
        logger.debug(f"Attempting to get route by name: '{name}'")
        for route in self.routes:
            if route.name == name:
                logger.debug(f"Found route by name: '{name}' -> '{route.path}'")
                return route
        logger.warning(f"Route with name '{name}' not found.")
        return None

    def remove_route(self, path: str, methods: Optional[List[str]] = None):
        """
        Removes a route or specific methods for a route based on path and optional methods.

        Args:
            path: The path of the route(s) to remove.
            methods: A list of specific HTTP methods to remove for the given path.
                     If None, all routes matching the path are removed.
        """
        logger.debug(f"Attempting to remove route(s) for path: '{path}' with methods: {methods}")
        methods_to_remove_upper = {m.upper() for m in methods} if methods is not None else None
        initial_route_count = len(self.routes)

        self.routes = [
            route for route in self.routes
            if not (
                route.path == path and (
                    methods_to_remove_upper is None or
                    (route.methods is not None and any(m in methods_to_remove_upper for m in route.methods)) 
                )
            )
        ]
        removed_count = initial_route_count - len(self.routes) 

        if removed_count > 0:
            logger.info(f"Removed {removed_count} route(s) for path: '{path}' and methods: {methods}")
        else:
            logger.warning(f"No routes found for removal matching path: '{path}' and methods: {methods}")

