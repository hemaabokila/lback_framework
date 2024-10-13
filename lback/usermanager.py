from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from lback.user import User
class UserManager:
    def __init__(self, session):
        self.session = session

    def register_user(self, username, email, password):
        if not username or not email or not password:
            raise ValueError("Username, Email, and Password are required.")
        if "@" not in email:
            raise ValueError("Invalid email format.")
        
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)

        try:
            user.save(self.session)
            return user
        except IntegrityError:
            self.session.rollback()
            raise ValueError("Username or Email already exists.")

    def authenticate_user(self, username, password):
        user = self.session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return user
        return None

    def update_user(self, user_id, **kwargs):
        user = self.session.query(User).get(user_id)
        if not user:
            raise ValueError("User not found.")
        
        for key, value in kwargs.items():
            setattr(user, key, value)
        
        user.save(self.session)
        return user

    def delete_user(self, user_id):
        user = self.session.query(User).get(user_id)
        if not user:
            raise ValueError("User not found.")
        user.delete(self.session)

    def reset_password(self, user_id, new_password):
        user = self.session.query(User).get(user_id)
        if not user:
            raise ValueError("User not found.")
        
        hashed_password = generate_password_hash(new_password)
        user.password = hashed_password
        user.save(self.session)

    def get_user_by_email(self, email):
        return self.session.query(User).filter_by(email=email).first()

    def get_all_users(self):
        return self.session.query(User).all()

    def search_users(self, **criteria):
        query = self.session.query(User)
        for key, value in criteria.items():
            query = query.filter(getattr(User, key) == value)
        return query.all()
