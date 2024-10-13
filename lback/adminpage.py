from lback.templates import render_template
from lback.adminauth import AdminAuth
from lback.user import User 
from lback.database import Session

class AdminPage:
    def __init__(self):
        self.auth = AdminAuth()

    def login_page(self):
        return render_template("admin_login.html")

    def login(self, username, password):
        if self.auth.login(username, password):
            return {"status_code": 302, "redirect": "/admin/dashboard"}
        else:
            return {"status_code": 400, "error": "Invalid credentials!"}

    def dashboard(self):
        users = self.get_all_users()  
        return render_template("admin_dashboard.html", users=users)

    def get_all_users(self):
        session = Session()
        try:
            users = session.query(User).all() 
        except Exception as e:
            print(f"Error retrieving users: {e}")
            users = []
        finally:
            session.close()
        return users

    def logout(self):
        self.auth.logout()
        return {"status_code": 302, "redirect": "/admin/login"}

    def delete_user(self, user_id):
        session = Session()
        try:
            user = session.query(User).filter_by(id=user_id).first() 
            if user:
                session.delete(user)
                session.commit()
                print(f"User {user_id} deleted successfully.")
                return {"status_code": 200, "message": "User deleted successfully."}
            else:
                print("User not found.")
                return {"status_code": 404, "error": "User not found."}
        except Exception as e:
            session.rollback()
            print(f"Error deleting user: {e}")
            return {"status_code": 500, "error": "Failed to delete user."}
        finally:
            session.close()

    def view_user(self, user_id):
        session = Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()  
            if user:
                return render_template("admin_user_detail.html", user=user)
            else:
                return {"status_code": 404, "error": "User not found."}
        except Exception as e:
            print(f"Error retrieving user details: {e}")
            return {"status_code": 500, "error": "Failed to retrieve user details."}
        finally:
            session.close()
