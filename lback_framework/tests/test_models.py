from lback.models.user import User
from lback.models.product import Product
from lback.models.adminuser import AdminUser
from lback.models import BaseModel

def test_user_model_create():
    user = User(username="testuser", email="test@example.com", password="pass")
    assert user.username == "testuser"
    assert user.email == "test@example.com"

def test_product_model_create():
    product = Product(name="Book", price=100)
    assert product.name == "Book"
    assert product.price == 100

def test_admin_user_model_create():
    admin = AdminUser(username="admin", email="admin@example.com", password="adminpass")
    assert admin.username == "admin"
    assert admin.email == "admin@example.com"

def test_base_model_save_and_delete():
    class DummyModel(BaseModel):
        def __init__(self, name):
            self.name = name

    obj = DummyModel(name="dummy")
    obj.save()
    assert hasattr(obj, "id")
    obj.delete()
