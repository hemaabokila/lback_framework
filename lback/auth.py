from lback.database import Session
from lback.user import User 
from datetime import datetime 

class AuthMiddleware:
    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return self._unauthorized_response()
        try:
            token_type, token = auth_header.split(" ")
            if token_type != 'Bearer' or not self.is_valid_token(token):
                return self._forbidden_response()
        except ValueError:
            return self._unauthorized_response()

    def process_response(self, request, response):
        return response

    def is_valid_token(self, token):
        session = Session()
        try:
            user = session.query(User).filter_by(auth_token=token).first()
            return user is not None and self._is_token_active(user)
        except Exception as e:
            print(f"Error validating token: {e}")
            return False
        finally:
            session.close()

    def _is_token_active(self, user):
        return user.token_expiry > datetime.utcnow()

    def _unauthorized_response(self):
        return {"status_code": 401, "body": "Unauthorized"}

    def _forbidden_response(self):
        return {"status_code": 403, "body": "Forbidden"}

