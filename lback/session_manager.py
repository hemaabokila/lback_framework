import uuid
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_timeout = timedelta(minutes=30) 

    def create_session(self, user_id):
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + self.session_timeout
        self.sessions[session_id] = {'user_id': user_id, 'expires_at': expires_at}
        return session_id

    def get_user(self, session_id):
        session = self.sessions.get(session_id)
        if session and not self.is_session_expired(session):
            return session['user_id']
        return None

    def is_session_expired(self, session):
        return datetime.utcnow() > session['expires_at']

    def delete_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def renew_session(self, session_id):
        session = self.sessions.get(session_id)
        if session:
            session['expires_at'] = datetime.utcnow() + self.session_timeout
            return True
        return False

    def cleanup_sessions(self):
        expired_sessions = [sid for sid, session in self.sessions.items() if self.is_session_expired(session)]
        for sid in expired_sessions:
            del self.sessions[sid]
