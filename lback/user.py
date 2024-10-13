from sqlalchemy import Column, String, Boolean
from werkzeug.security import generate_password_hash, check_password_hash
import re
from lback.models import BaseModel
class User(BaseModel):
    __tablename__ = 'users'
    
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    def validate(self):
        """Validate user attributes."""
        if not self.username or not self.email or not self.password:
            raise ValueError("Username, Email, and Password are required.")
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if len(self.password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise ValueError("Invalid email format.")

    def set_password(self, password):
        """Set hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check the hashed password."""
        return check_password_hash(self.password, password)
    

    @classmethod
    def get_fields(cls):
        return {column.name: str(column.type) for column in cls.__table__.columns}

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, is_active={self.is_active})>"
