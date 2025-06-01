import logging
from typing import Dict, Any, Optional, List
from http import HTTPStatus
from sqlalchemy.orm import Session as DBSession

from lback.core.response import Response
from lback.core.types import Request, HTTPMethod
from lback.utils.shortcuts import render, redirect, return_500
from lback.auth.permissions import PermissionRequired
from lback.auth.adminauth import AdminAuth
from lback.models.adminuser import AdminUser
from lback.utils.app_session import AppSession
from lback.core.templates import TemplateNotFound



logger = logging.getLogger(__name__)

def admin_login_page(request: Request) -> Response:
    """
    Renders the admin login page.
    Simplified using render helper and request properties.
    Updated to use new error shortcuts.
    """
    logger.info("Rendering admin login page.")

    try:
        if request.user and isinstance(request.user, AdminUser):
            logger.info("Admin user already logged in. Redirecting to dashboard.")
            if request.session:
                request.session.set_flash("You are already logged in.", "info")
            return redirect("/admin/dashboard/")

        context: Dict[str, Any] = {}

        if request.session:
            context['flash_messages'] = request.session.get_flashed_messages()
        else:
            context['flash_messages'] = []
            logger.debug("request.session is missing in admin_login_page. Flash messages will not be displayed.")


        return render(request, "admin/login.html", context)

    except TemplateNotFound:

        logger.error(f"Admin login template 'admin/login.html' not found.")
        raise

    except Exception as e:
        logger.exception("Error rendering admin login page.")

        if request.session:
             request.session.set_flash("An internal error occurred.", "danger")
        return return_500(request, exception=e)


def admin_login_post(request: Request) -> Response:
    """
    Handles the submission of the admin login form.
    Authenticates the admin user and redirects to the dashboard on success.
    Simplified using redirect helper and request properties.
    Updated to use new error shortcuts and leverage request.POST/request.DATA.
    """
    logger.info(f"Handling admin login POST submission for method: {request.method}")

    admin_manager = request.admin_user_manager
    session_manager = request.session_manager
    db_session: Optional[DBSession] = request.db_session
    user_session: Optional[AppSession] = request.session
    config = request.config

    if admin_manager is None or session_manager is None or config is None:
         logger.critical("Missing core dependencies (admin_manager, session_manager, config) in admin_login_post.")
         return return_500(request, message="Internal Server Error: Core dependencies missing.")

    if db_session is None:
        logger.error("Database session not found on request context in admin_login_post.")
        return return_500(request, message="Internal Server Error: Database session not available.")

    if user_session is None:
        logger.error("Session object not found on request context in admin_login_post.")
        return return_500(request, message="Internal Server Error: Session not available.")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Received non-POST request for login submission: {request.method}")
        if request.error_handler:
             return request.error_handler.handle_405(request, allowed_methods=[HTTPMethod.POST.value])
        else:
             return Response(body=b"Method Not Allowed", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, headers={'Content-Type': 'text/plain', 'Allow': HTTPMethod.POST.value})


    form_data: Dict[str, Any] = request.POST

    if not isinstance(form_data, dict):
         logger.warning(f"admin_login_post: request.POST did not return a dictionary. Type: {type(form_data)}. Expected dict.")
         if user_session: user_session.set_flash("Invalid request data for login.", "error")
         return redirect("/admin/login/")

    username: Optional[str] = form_data.get('username')
    password: Optional[str] = form_data.get('password')

    logger.debug(f"admin_login_post: Extracted data from request.POST: username={username}, password present: {password is not None}")

    if not username or not password:
        logger.warning("admin_login_post: Missing username or password after extracting from request.POST.")
        if user_session: user_session.set_flash("Username and password are required.", "warning")
        return redirect("/admin/login/")

    try:
        admin_auth_instance = AdminAuth(
            admin_user_manager=admin_manager,
            session_manager=session_manager
        )

        authenticated_admin_user = admin_auth_instance.login(request, db_session, username, password)

        if authenticated_admin_user:
            logger.info(f"Admin login successful for user: {username}. Redirecting to dashboard.")
            if user_session: user_session.set_flash("Login successful!", "success")
            return redirect("/admin/dashboard/")
        else:
            logger.warning(f"Admin login failed for user: {username}. Invalid credentials.")
            return redirect("/admin/login/")

    except Exception as e:
        logger.exception(f"Error during admin login process for user {username}.")
        if user_session: user_session.set_flash(f"An error occurred during login.", "danger")
        return return_500(request, exception=e)


@PermissionRequired("view_dashboard")
def admin_dashboard_page(request: Request) -> Response:
    """
    Displays the admin dashboard page.
    Requires authentication and 'view_dashboard' permission.
    Simplified using render helper and request properties.
    Updated to use new error shortcuts.
    """
    logger.info(f"Rendering admin dashboard page for path: {request.path}")
    admin_registry = request.admin_registry

    if admin_registry is None:
        logger.critical("Missing AdminRegistry dependency in admin_dashboard_page.")
        return return_500(request, message="Internal Server Error: Admin registry missing.")

    try:
        registered_models_names: List[str] = []
        if hasattr(admin_registry, 'get_registered_models') and callable(admin_registry.get_registered_models):
            try:
                 registered_models_raw = admin_registry.get_registered_models()
                 if isinstance(registered_models_raw, dict):
                     registered_models_names = list(registered_models_raw.keys())
                 elif isinstance(registered_models_raw, list):
                     registered_models_names = [model.__name__ for model in registered_models_raw if hasattr(model, '__name__')]
                 logger.debug(f"Successfully retrieved registered models from AdminRegistry. Count: {len(registered_models_names)}")
            except Exception as reg_e:
                 logger.error(f"Error accessing registered models from AdminRegistry: {reg_e}", exc_info=True)
                 registered_models_names = []
        else:
            logger.warning("AdminRegistry does not have a standard method like get_registered_models(). Cannot list models.")

        context: Dict[str, Any] = {
             "registered_models": registered_models_names,
        }
        return render(request, "admin/admin_dashboard.html", context)

    except TemplateNotFound:
        logger.error(f"Dashboard template 'admin/admin_dashboard.html' not found.")
        raise 

    except Exception as e:
        logger.exception(f"Error rendering admin dashboard page.")
        if request.session:
             request.session.set_flash("An internal error occurred.", "danger")
        return return_500(request, exception=e)


def admin_logout_post(request: Request) -> Response:
    """
    Handles admin logout.
    Requires authentication.
    Simplified using redirect helper and request properties.
    Updated to use new error shortcuts.
    """
    logger.info("Handling admin logout POST submission.")

    user_session = request.session

    if user_session is None:
        logger.warning("UserSession dependency is missing in admin_logout_post. Cannot perform logout.")
        return redirect("/admin/login/")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Received non-POST request for logout submission: {request.method}")
        if request.error_handler:
             return request.error_handler.handle_405(request, allowed_methods=[HTTPMethod.POST.value])
        else:
             return Response(body=b"Method Not Allowed", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, headers={'Content-Type': 'text/plain', 'Allow': HTTPMethod.POST.value})
    try:
        user_session.delete()
        logger.info(f"Admin user logged out successfully.")
        user_session.set_flash("You have been logged out.", "success")
        return redirect("/admin/login/")
    
    
    except Exception as e:
        logger.exception("Error during admin logout process.")
        if user_session: user_session.set_flash(f"An error occurred during logout.", "danger")
        return return_500(request, exception=e)