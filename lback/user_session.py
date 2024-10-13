class UserSession:
    def __init__(self, user):
        self.user = user
        self.is_active = True
        self.session_data = {} 

    def set_data(self, key, value):
        self.session_data[key] = value

    def get_data(self, key):
        return self.session_data.get(key)

    def clear_data(self):
        self.session_data.clear()

    def end_session(self):
        self.is_active = False
        self.clear_data()

    def is_active_session(self):
        return self.is_active

    def __str__(self):
        return f"UserSession(user={self.user}, is_active={self.is_active}, session_data={self.session_data})"
