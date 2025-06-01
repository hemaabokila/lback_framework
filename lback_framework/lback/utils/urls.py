from typing import List, Optional, Callable, Any

from lback.core.types import Request



def path(pattern: str,
         view_function: Callable[[Request, ...], Any],
         allowed_methods: Optional[List[str]] = None,
         name: Optional[str] = None,
         requires_auth: bool = False
        ) -> tuple:
    """
    Helper function to define a URL pattern tuple for the router.

    Args:
        pattern: The URL pattern string (e.g., '/about/', '/users/{user_id:int}/', '/courses/course/{course_slug}/videos/').
        view_function: The Python function that handles the request for this pattern.
        allowed_methods: A list of allowed HTTP methods (e.g., ['GET', 'POST']). Defaults to ['GET'] if not provided.
        name: An optional name for the URL pattern, used for reverse lookups.
        requires_auth: Boolean indicating if the route requires authentication. Defaults to False.

    Returns:
        A tuple (pattern, view_function, allowed_methods, name, requires_auth)
        representing the URL pattern definition, suitable for the router's urlpatterns list.
    """
    if allowed_methods is None:
        allowed_methods = ["GET"]


    allowed_methods = [method.upper() for method in allowed_methods]
    return (pattern, view_function, allowed_methods, name, requires_auth)

