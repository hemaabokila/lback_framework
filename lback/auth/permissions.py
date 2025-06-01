import logging
from typing import List, Union, Set, Callable, Any
from functools import wraps

from lback.core.types import Request
from lback.core.response import Response
from lback.core.signals import dispatcher
from lback.utils.shortcuts import redirect, return_403


logger = logging.getLogger(__name__)


class PermissionRequired:
    """
    Decorates views to ensure the authenticated user has the necessary permissions.
    It checks for superuser status or individual permissions via the user's has_permission method.
    """
    def __init__(self, required_permissions: Union[str, List[str], Set[str], Callable[[Request], Union[str, List[str], Set[str]]]]):
        """
        Initializes the decorator with the permission(s) needed.
        """
        self.required_permissions = required_permissions
        self.dynamic = callable(required_permissions)
        logger.debug(f"PermissionRequired initialized. Dynamic: {self.dynamic}, Value: {self.required_permissions}")

    def has_permission(self, user: Any, required_permissions: Set[str]) -> bool:
        """
        Checks if the user possesses the required permissions.
        This method now directly uses the `has_permission` method from the user model.
        """

        if not user:
            logger.debug("Permission check failed: User object is None (not authenticated).")
            return False

        if hasattr(user, "is_superuser") and user.is_superuser:
            logger.debug("Permission granted: User is a superuser.")
            return True

        if hasattr(user, "has_permission") and callable(user.has_permission):
            for perm in required_permissions:
                if not user.has_permission(perm):
                    logger.debug(f"Permission denied: User '{user.username}' missing permission '{perm}'.")
                    return False
                
            logger.debug(f"Permission granted: User '{user.username}' has all required permissions: {required_permissions}.")
            return True
        else:
            logger.error(f"Permission check failed: User object '{type(user).__name__}' does not have a callable 'has_permission' method.")
            return False

    def __call__(self, func: Callable) -> Callable:
        """
        The decorator logic. Wraps the view function to perform permission checks.
        """

        @wraps(func)
        def wrapper(request: Request, *args, **kwargs) -> Response:
            view_func_name = getattr(func, '__name__', str(func))
            logger.debug(f"Checking permissions for view: {view_func_name}")

            if self.dynamic:
                computed_permissions_raw = self.required_permissions(request)
                if isinstance(computed_permissions_raw, str):
                    computed_permissions = {computed_permissions_raw}
                elif isinstance(computed_permissions_raw, (list, set)):
                    computed_permissions = set(computed_permissions_raw)
                else:
                    logger.error(f"Dynamic permissions callable for '{view_func_name}' returned invalid type: {type(computed_permissions_raw)}. Expected string, list, or set.")
                    computed_permissions = set()
            else:
                if isinstance(self.required_permissions, str):
                    computed_permissions = {self.required_permissions}
                elif isinstance(self.required_permissions, (list, set)):
                    computed_permissions = set(self.required_permissions)
                else:
                    logger.error(f"Static required_permissions for '{view_func_name}' is invalid type: {type(self.required_permissions)}. Expected string, list, or set.")
                    computed_permissions = set()

            user = getattr(request, "user", None)
            dispatcher.send("permission_check_started", sender=self, request=request, required_permissions=computed_permissions, user=user, view_func_name=view_func_name)
            logger.debug(f"Signal 'permission_check_started' sent for '{view_func_name}'. Required: {computed_permissions}")

            has_permission_result = self.has_permission(user, computed_permissions)

            if has_permission_result:
                logger.debug(f"Permission granted for view: {view_func_name}")
                dispatcher.send("permission_check_succeeded", sender=self, request=request, required_permissions=computed_permissions, user=user, view_func_name=view_func_name)
                logger.debug(f"Signal 'permission_check_succeeded' sent for '{view_func_name}'.")
                return func(request, *args, **kwargs)
            
            else:
                logger.warning(f"Permission denied for view: {view_func_name}. User: {user}. Required: {computed_permissions}")
                reason = "unknown"
                if user is None:
                    reason = "user_not_authenticated"
                elif not hasattr(user, "has_permission") or not callable(user.has_permission):
                    reason = "user_model_missing_has_permission_method"

                dispatcher.send("permission_check_failed", sender=self, request=request, required_permissions=computed_permissions, user=user, view_func_name=view_func_name, reason=reason)
                logger.debug(f"Signal 'permission_check_failed' sent for '{view_func_name}'. Reason: {reason}")

                if user is None:
                    request.session.set_flash("You must be logged in to access this page.", "warning")
                    return redirect("/auth/login/")

                request.session.set_flash("You do not have permission to access this page.", "danger")
                return return_403(request, message="Permission Denied")

        return wrapper