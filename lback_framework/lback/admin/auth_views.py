import logging
from typing import Dict, Any, Optional
from http import HTTPStatus
from lback.auth.password_hashing import PasswordHasher
from sqlalchemy.orm import Session as SQLASession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from lback.core.response import Response
from lback.core.types import Request, HTTPMethod
from lback.core.config import Config
from lback.models.adminuser import AdminUser, Role
from lback.utils.shortcuts import render, redirect, return_404, return_500
from lback.auth.permissions import PermissionRequired

logger = logging.getLogger(__name__)

@PermissionRequired("add_adminuser")
def admin_user_add_view(request: Request) -> Response:
    """
    View to add a new AdminUser object.
    Handles both GET (display form) and POST (process form).
    """
    logger.info(f"Handling admin_user_add_view for {request.method} {request.path}.")
    db_session: Optional[SQLASession] = request.db_session
    config: Optional[Config] = request.config

    if not db_session or not config:
        logger.critical("Database session or Config is not available in admin_user_add_view.")
        return return_500(request, message="Internal Server Error: Missing dependencies.")

    current_user: Optional[AdminUser] = request.user
    if not current_user or not current_user.is_superuser: 
        logger.warning(f"Non-superuser {current_user.username if current_user else 'anonymous'} attempted to access admin_user_add_view.")
        return return_404(request, message="You do not have permission to add new users.")


    admin_user_obj = AdminUser()
    form_errors: Dict[str, str] = {}
    error_message: Optional[str] = None

    if request.method == HTTPMethod.POST:
        logger.info("admin_user_add_view: Processing POST request.")
        form_data: Dict[str, Any] = request.parsed_body if hasattr(request, 'parsed_body') and request.parsed_body is not None else {}

        username = form_data.get('username', '').strip()
        email = form_data.get('email', '').strip()
        password = form_data.get('password', '')
        is_superuser_from_form = form_data.get('is_superuser') == 'on' 
        role_id_str = form_data.get('role_id', '')

        is_superuser = is_superuser_from_form if current_user.is_superuser else False


        if not username:
            form_errors['username'] = 'Username is required.'
        if not email:
            form_errors['email'] = 'Email is required.'
        if not password:
            form_errors['password'] = 'Password is required.'

        admin_user_obj.username = username
        admin_user_obj.email = email
        admin_user_obj.is_superuser = is_superuser
        try:
            admin_user_obj.role_id = int(role_id_str) if role_id_str else None
        except ValueError:
            form_errors['role_id'] = 'Invalid role ID.'
            admin_user_obj.role_id = None 


        if not form_errors:
            try:
                hashed_password = PasswordHasher.hash_password(password)
                admin_user_obj.password = hashed_password

                role = None
                if admin_user_obj.role_id is not None:
                    role = db_session.query(Role).get(admin_user_obj.role_id)
                    if not role:
                        form_errors['role_id'] = 'Selected role not found.'
                        admin_user_obj.role_id = None

                if not form_errors:
                    db_session.add(admin_user_obj)
                    db_session.commit()

                    logger.info(f"AdminUser added successfully with ID {admin_user_obj.id}.")
                    return redirect("/admin/adminuser/")

            except IntegrityError as e:
                db_session.rollback()
                logger.error(f"AdminUser add: Database integrity error: {e}", exc_info=True)
                if "admin_users_username_key" in str(e):
                    form_errors['username'] = 'Username already exists.'
                elif "admin_users_email_key" in str(e):
                    form_errors['email'] = 'Email already exists.'
                else:
                    form_errors['_general'] = 'Database error: Could not save user.'
                    error_message = "Database error: Could not save user due to integrity constraint."

            except Exception as e:
                db_session.rollback()
                logger.exception(f"AdminUser add: Error saving user: {e}.")
                form_errors['_general'] = 'An unexpected error occurred.'
                error_message = f"An unexpected error occurred: {e}"

        if form_errors or error_message:
            logger.warning("AdminUser add: Form has errors, re-rendering form.")
            roles = db_session.query(Role).all()
            roles_choices = [{'id': role.id, 'text': str(role)} for role in roles]

            form_fields_data = [
                {'name': 'username', 'label': 'Username', 'type': 'string', 'nullable': False, 'current_value': admin_user_obj.username},
                {'name': 'email', 'label': 'Email', 'type': 'string', 'nullable': False, 'current_value': admin_user_obj.email},
                {'name': 'password', 'label': 'Password', 'type': 'password', 'nullable': False, 'current_value': ''},
                {'name': 'is_superuser', 'label': 'Is Superuser', 'type': 'boolean', 'nullable': True, 'current_value': admin_user_obj.is_superuser},
                {'name': 'role_id', 'label': 'Role', 'type': 'manytoone', 'nullable': True, 'current_value': admin_user_obj.role_id},
            ]

            relationship_fields_data = {
                'role_id': {'field_name': 'role_id', 'relation_name': 'role', 'type': 'manytoone', 'related_model_name': 'Role', 'choices': roles_choices, 'nullable': True}
            }

            context = {
                "model_name": "AdminUser",
                "is_add": True,
                "object": admin_user_obj,
                "form_fields_data": form_fields_data,
                "relationship_fields_data": relationship_fields_data,
                "form_errors": form_errors,
                "error_message": error_message,
                "router": request.router,
                "config": request.config,
                "request": request,
                "current_user": current_user 
            }
            return render(request, "admin/auth/adminuser_form.html", context, status_code=HTTPStatus.BAD_REQUEST.value if form_errors else HTTPStatus.INTERNAL_SERVER_ERROR.value)


    else:
        logger.info("admin_user_add_view: Displaying add form.")

        try:
            roles = db_session.query(Role).all()
            roles_choices = [{'id': role.id, 'text': str(role)} for role in roles]

            form_fields_data = [
                {'name': 'username', 'label': 'Username', 'type': 'string', 'nullable': False, 'current_value': ''},
                {'name': 'email', 'label': 'Email', 'type': 'string', 'nullable': False, 'current_value': ''},
                {'name': 'password', 'label': 'Password', 'type': 'password', 'nullable': False, 'current_value': ''},
                {'name': 'is_superuser', 'label': 'Is Superuser', 'type': 'boolean', 'nullable': True, 'current_value': False},
                {'name': 'role_id', 'label': 'Role', 'type': 'manytoone', 'nullable': True, 'current_value': None},
            ]
            

            relationship_fields_data = {
                'role_id': {'field_name': 'role_id', 'relation_name': 'role', 'type': 'manytoone', 'related_model_name': 'Role', 'choices': roles_choices, 'nullable': True}
            }

            context = {
                "model_name": "AdminUser",
                "is_add": True,
                "object": admin_user_obj,
                "form_fields_data": form_fields_data,
                "relationship_fields_data": relationship_fields_data,
                "form_errors": {},
                "error_message": None,
                "router": request.router,
                "config": request.config,
                "request": request,
                "current_user": current_user
            }
            return render(request, "admin/auth/adminuser_form.html", context)

        except Exception as e:
            logger.exception("Error rendering admin_user_add_view form.")
            return return_500(request, exception=e)
        
        
@PermissionRequired("view_adminuser")
def admin_user_list_view(request: Request) -> Response:
    """
    View to list AdminUser objects with precise access control for display.
    """
    logger.info(f"Handling admin_user_list_view for {request.method} {request.path}.")
    db_session: Optional[SQLASession] = request.db_session

    if not db_session:
        logger.critical("Database session is not available in admin_user_list_view.")
        return return_500(request, message="Internal Server Error: Missing database session.")

    current_user: Optional[AdminUser] = request.user 

    if not current_user:
        logger.warning("No user logged in for admin_user_list_view. Redirecting to login.")
        return redirect("/admin/login")

    query = db_session.query(AdminUser)
    admin_users = []

    if current_user.id == 1:
        admin_users = query.order_by(AdminUser.id).all()
        logger.info(f"Admin ID 1 viewing all users.")
    elif current_user.is_superuser:
        admin_users = query.filter(
            or_(
                AdminUser.id == current_user.id,
                AdminUser.is_superuser == False
            )
        ).order_by(AdminUser.id).all()
        logger.info(f"Superuser '{current_user.username}' viewing self and all non-superusers.")
    else:
        admin_users = [current_user]
        logger.info(f"Regular user '{current_user.username}' viewing only self.")

    can_add_adminuser = current_user.is_superuser

    context = {
        "model_name": "AdminUser",
        "admin_users": admin_users,
        "can_add_adminuser": can_add_adminuser, 
        "current_user_id": current_user.id, 
        "is_current_user_superuser": current_user.is_superuser, 
        "router": request.router,
        "config": request.config,
        "request": request,
    }
    return render(request, "admin/auth/adminuser_list.html", context)

