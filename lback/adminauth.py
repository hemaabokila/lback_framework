from lback.database import Session
from lback.models import User
import bcrypt
import re
class AdminAuth:
    def __init__(self):
        self.session = Session()

    def register(self, username, email, password):
        if not username or not email or not password:
            print("All fields are required!")
            return False
        
        if not self._is_valid_email(email):
            print("Invalid email format!")
            return False
        
        if self._is_username_taken(username):
            print("Username already exists!")
            return False
        
        if self._is_email_taken(email):
            print("Email already exists!")
            return False

        new_user = User(username=username, email=email)
        new_user.password = self._hash_password(password)
        
        self._add_user_to_db(new_user)
        print("User registered successfully!")
        return True

    def login(self, username, password):
        user = self.session.query(User).filter_by(username=username).first()
        
        if user and self._verify_password(password, user.password):
            print("Login successful!")
            return True
        
        print("Invalid username or password!")
        return False

    def _is_username_taken(self, username):
        return self.session.query(User).filter_by(username=username).first() is not None

    def _is_email_taken(self, email):
        return self.session.query(User).filter_by(email=email).first() is not None

    def _add_user_to_db(self, user):
        try:
            self.session.add(user)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Error adding user to database: {e}")
        finally:
            self.session.close()

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password, hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def _is_valid_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def logout(self):
        print("User logged out successfully!")

