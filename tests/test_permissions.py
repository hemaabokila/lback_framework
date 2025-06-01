from lback.auth.permissions import PermissionRequired

class DummyUser:
    def __init__(self, permissions):
        self.permissions = permissions

def test_permission_required_allows():
    perm = PermissionRequired("edit")
    user = DummyUser(permissions=["edit", "view"])
    assert perm.has_permission(user) is True

def test_permission_required_denies():
    perm = PermissionRequired("delete")
    user = DummyUser(permissions=["edit", "view"])
    assert perm.has_permission(user) is False