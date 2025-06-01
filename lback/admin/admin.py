from lback.models.adminuser import AdminUser, Permission, Role
from lback.models.user import User, Group, UserPermission
from lback.admin.registry import admin

admin.register(AdminUser)
admin.register(Permission)
admin.register(Role)
admin.register(User)
admin.register(Group)
admin.register(UserPermission)

