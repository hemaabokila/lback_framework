
from lback.utils.urls import path

from .auth_views import (
    register_user_view as api_register_user_view,
    login_user_view as api_login_user_view,
    verify_email_view as api_verify_email_view,
    request_password_reset_view as api_request_password_reset_view,
    reset_password_view as api_reset_password_view
)

from .web_auth_views import (
    show_register_page,
    handle_register_submit,
    show_login_page,
    handle_login_submit,
    show_request_password_reset_page,
    handle_request_password_reset_submit,
    show_reset_password_confirm_page,
    handle_reset_password_confirm_submit,
    verify_email_web_view,
    logout_user_view
)

urlpatterns = [
    path("api/auth/register/", api_register_user_view, allowed_methods=["POST"], name="api_register_user", requires_auth=False),
    path("api/auth/login/", api_login_user_view, allowed_methods=["POST"], name="api_login_user", requires_auth=False),
    path("api/auth/verify-email/", api_verify_email_view, allowed_methods=["GET"], name="api_verify_email", requires_auth=False),
    path("api/auth/request-reset-password/", api_request_password_reset_view, allowed_methods=["POST"], name="api_request_reset_password", requires_auth=False),
    path("api/auth/reset-password/", api_reset_password_view, allowed_methods=["POST"], name="api_reset_password", requires_auth=False),


    path("register/", show_register_page, allowed_methods=["GET"], name="web_register_page", requires_auth=False),
    path("auth/register/", handle_register_submit, allowed_methods=["POST"], name="web_handle_register_submit", requires_auth=False),
    path("login/", show_login_page, allowed_methods=["GET"], name="web_login_page", requires_auth=False),
    path("auth/login/", handle_login_submit, allowed_methods=["POST"], name="web_handle_login_submit", requires_auth=False),
    path("request-reset-password/", show_request_password_reset_page, allowed_methods=["GET"], name="web_request_reset_password_page", requires_auth=False),
    path("auth/request-reset-password/", handle_request_password_reset_submit, allowed_methods=["POST"], name="web_handle_request_reset_password_submit", requires_auth=False),
    path("reset-password-confirm/", show_reset_password_confirm_page, allowed_methods=["GET"], name="web_reset_password_confirm_page", requires_auth=False),
    path("auth/reset-password/", handle_reset_password_confirm_submit, allowed_methods=["POST"], name="web_handle_reset_password_confirm_submit", requires_auth=False),
    path("verify-email/", verify_email_web_view, allowed_methods=["GET"], name="web_verify_email", requires_auth=False),
    path("logout/", logout_user_view, allowed_methods=["POST"], name="web_logout_user", requires_auth=True),
    path("logout/", logout_user_view, allowed_methods=["GET"], name="web_logout_user_get", requires_auth=True),

]

