# """Lback: web framework."""
# from lback.admin.admin import admin
# from lback.admin.auth_views import admin_user_add_view, admin_user_list_view
# from lback.admin.generic import generic_add_view, generic_list_view, generic_delete_view, generic_change_view, generic_detail_view
# from lback.admin.registry import AdminRegistry
# from lback.admin.urls import urlpatterns
# from lback.admin.views import admin_login_page, admin_dashboard_page, admin_login_post, admin_logout_post,
# from lback.api.docs import APIDocs
# from lback.api.generics import (
#     GenericAPIView,
#     ListAPIView,
#     CreateAPIView,
#     RetrieveAPIView,
#     UpdateAPIView,
#     DestroyAPIView,
#     ListCreateAPIView,
#     RetrieveUpdateDestroyAPIView,
# )
# from lback.api.mixins import (
#     ListModelMixin,
#     CreateModelMixin,
#     RetrieveModelMixin,
#     UpdateModelMixin,
#     DestroyModelMixin,
# )
# from lback.api.serializer import Field, BooleanField, BaseModelSerializer, IntegerField, StringField, RelatedField, DateTimeField
# from lback.api.view import APIView, BaseView
# from lback.auth.session_auth import SessionAuth
# from lback.auth.permissions import PermissionRequired
# from lback.auth.password_hashing import PasswordHasher
# from lback.auth.oauth import OAuth2Auth
# from lback.auth.jwt_auth import JWTAuth
# from lback.auth.adminauth import AdminAuth
# from lback.auth_app.web_auth_views import (
#     show_login_page,
#     show_register_page,
#     show_reset_password_confirm_page,
#     show_request_password_reset_page,
#     handle_login_submit,
#     handle_register_submit,
#     handle_reset_password_confirm_submit,
#     handle_request_password_reset_submit,
#     verify_email_web_view,
#     logout_user_view
# )
# from lback.auth_app.urls import urlpatterns
# from lback.auth_app.auth_views import (
#     register_user_view,
#     login_user_view,
#     request_password_reset_view,
#     reset_password_view,
#     verify_email_view,
# )
# from lback.commands.admin import AdminCommands
# from lback.commands.app import AppCommands
# from lback.commands.db_seed import setup_database_and_defaults
# from lback.commands.migration import MigrationCommands
# from lback.commands.project import ProjectCommands
# from lback.commands.runner import RunnerCommands
# from lback.core.app_controller import AppController
# from lback.core.base_middleware import BaseMiddleware
# from lback.core.cache import Cache, CacheItem
# from lback.core.config_manager import SettingsFileHandler, load_config, load_settings_module, update_config, start_settings_watcher, sync_settings_to_config, get_project_root
# from lback.core.config import Config
# from lback.core.dispatcher_instance import dispatcher
# from lback.core.error_handler import ErrorHandler
# from lback.core.exceptions import FrameworkException, Forbidden, HTTPException, BadRequest, NotFound, RouteNotFound, MethodNotAllowed, Unauthorized, ConfigurationError, ValidationError, RouteNotFound, ServerError
# from lback.core.logging_setup import setup_logging
# from lback.core.middleware_loader import load_middlewares_from_config, create_middleware, import_class
# from lback.core.middleware_manager import MiddlewareManager, Middleware
# from lback.core.response import RedirectResponse, Response, HTMLResponse, JSONResponse
# from lback.core.router import Route, Router
# from lback.core.server import Server, initialize_core_components, wsgi_application
# from lback.core.signals import SignalDispatcher
# from lback.core.templates import TemplateRenderer, default_global_context, custom_uppercase, custom_url_tag
# from lback.core.types import Request, HTTPMethod, TypeConverter, UploadedFile, UUIDConverter, IntegerConverter
# from lback.core.urls_utils import Include
# from lback.core.websocket import WebSocketServer
# from lback.core.wsgi_entry import create_wsgi_app, setup_logging
# from lback.forms.fields_datetime import DateTimeField, TimeField, DateField
# from lback.forms.fields_file import FileField
# from lback.forms.fields import (
#     BooleanField,
#     CharField,
#     ChoiceField,
#     EmailField,
#     IntegerField,
# )
# from lback.forms.forms import Form, FormMetaclass
# from lback.forms.models import ModelForm
# from lback.forms.validation import (
#     ValidationError,
# )
# from lback.forms.widgets_datetime import DateInput, DateTimeInput, TextInput
# from lback.forms.widgets_file import FileInput
# from lback.forms.widgets import TextInput, Textarea, PasswordInput, CheckboxInput, Select
# from lback.middlewares.auth_midlewares import AuthMiddleware
# from lback.middlewares.body_parsing_middleware import BodyParsingMiddleware
# from lback.middlewares.cors import CORSMiddleware
# from lback.middlewares.csrf import CSRFMiddleware
# from lback.middlewares.debug import DebugMiddleware
# from lback.middlewares.logger import LoggingMiddleware
# from lback.middlewares.media_files_middleware import MediaFilesMiddleware
# from lback.middlewares.security_middleware import SecurityHeadersConfigurator, SecurityHeadersMiddleware, SQLInjectionDetectionMiddleware, SQLInjectionProtection
# from lback.middlewares.session_middleware import SessionMiddleware
# from lback.middlewares.sqlalchemy_middleware import SQLAlchemySessionMiddleware
# from lback.middlewares.static_files_middleware import StaticFilesMiddleware
# from lback.middlewares.timer import TimerMiddleware
# from lback.models.adminuser import AdminUser, Role, Permission
# from lback.models.base import BaseModel
# from lback.models.database import DatabaseManager
# from lback.models.product import Product
# from lback.models.session import Session
# from lback.models.user import User, Group, UserPermission
# from lback.repositories.admin_user_repository import AdminUserRepository
# from lback.repositories.permission_repository import PermissionRepository
# from lback.repositories.role_repository import RoleRepository
# from lback.repositories.user_repository import UserRepository
# from lback.security.firewall import AdvancedFirewall
# from lback.security.headers import SecurityHeadersConfigurator
# from lback.security.rate_limiter import RateLimiter
# from lback.security.sql_injection import SQLInjectionProtection
# from lback.utils.admin_user_manager import AdminUserManager
# from lback.utils.app_session import AppSession
# from lback.utils.email_sender import EmailSender
# from lback.utils.file_handlers import validate_uploaded_file, save_uploaded_file, delete_saved_file
# from lback.utils.filters import file_extension_filter, split_filter, date_filter
# from lback.utils.response_helpers import json_response
# from lback.utils.session_manager import SessionManager
# from lback.utils.shortcuts import render, redirect, return_403, return_404, return_500, _get_model_form_data, paginate_query, json_response
# from lback.utils.static_files import static, find_static_file
# from lback.utils.urls import path
# from lback.utils.user_manager import UserManager
# from lback.utils.validation import ValidationError, PasswordValidator, validate_json
