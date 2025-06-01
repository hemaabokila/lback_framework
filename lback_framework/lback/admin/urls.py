from lback.utils.urls import path
from . import auth_views

from .views import (
    admin_login_page,
    admin_login_post,
    admin_dashboard_page,
    admin_logout_post,
)

from .generic import (
    generic_add_view,
    generic_change_view,
    generic_delete_view,
    generic_list_view,
    generic_detail_view,
)


urlpatterns = [

    path("login/", admin_login_page, allowed_methods=["GET"], name="admin_login_page", requires_auth=False),
    path("login/", admin_login_post, allowed_methods=["POST"], name="admin_login_post", requires_auth=False),
    path("dashboard/", admin_dashboard_page, allowed_methods=["GET"], name="admin_dashboard", requires_auth=True),
    path("logout/", admin_logout_post, allowed_methods=["POST"], name="admin_logout", requires_auth=False),

    path("adminuser/add/", auth_views.admin_user_add_view, allowed_methods=["GET", "POST"], name="admin_user_add", requires_auth=True),
    path("adminuser/", auth_views.admin_user_list_view, allowed_methods=["GET"], name="admin_user_list", requires_auth=True),

    path("{model_name}/add/", generic_add_view, allowed_methods=["GET", "POST"], name="admin_add", requires_auth=True),
    path("{model_name}/{object_id:int}/change/", generic_change_view, allowed_methods=["GET", "POST"], name="admin_change", requires_auth=True),
    path("{model_name}/{object_id:int}/delete/", generic_delete_view, allowed_methods=["POST"], name="admin_delete", requires_auth=True),
    path("{model_name}/", generic_list_view, allowed_methods=["GET"], name="admin_list", requires_auth=True),
    path("{model_name}/{object_id:int}/", generic_detail_view, allowed_methods=["GET"], name="admin_detail", requires_auth=True),
    
]