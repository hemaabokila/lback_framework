import logging
from http import HTTPStatus
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session 

from lback.core.response import Response, JSONResponse
from lback.core.types import Request
from lback.utils.user_manager import UserManager
from lback.auth.jwt_auth import JWTAuth
from lback.utils.app_session import AppSession 
from lback.utils.validation import ValidationError

logger = logging.getLogger(__name__)

def register_user_view(request: Request, user_manager: UserManager, db_session: Session, app_session: AppSession) -> Response:
    """
    Handles user registration requests.
    Expects JSON body with 'username', 'email', 'password'.
    """
    logger.info(f"Received registration request for path: {request.path}")
    if request.method != "POST":
        logger.warning(f"Invalid method for /auth/register: {request.method}")
        return JSONResponse(status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, data={"message":  "Method Not Allowed"})

    try:
        data: Optional[Dict[str, Any]] = request.parsed_body 
        if not data:
            logger.warning("Registration request with no JSON body.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "JSON body is required."})

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            logger.warning("Missing required fields for registration.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "Username, email, and password are required."})


        user = user_manager.register_user(db_session, username, email, password)

        if user:
            db_session.commit()
            app_session.set_flash("Registration successful. Please check your email to verify your account.", "success")
            logger.info(f"User '{username}' registered successfully.")
            return JSONResponse(status_code=HTTPStatus.CREATED.value, data ={"message": "User registered successfully. Please verify your email."})
        else:

            db_session.rollback() 
            app_session.set_flash("Registration failed. Please try again or contact support.", "error")
            logger.error(f"Failed to register user '{username}'.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": "Registration failed. Username or email might already be taken."})

    except ValidationError as e:
        logger.warning(f"Validation error during user registration: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": str(e)})

    except ValueError as e:
        logger.critical(f"Critical error during user registration: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, data ={"message": "Internal Server Error: Default user group not found. Please contact support."})

    except Exception as e:
        logger.exception(f"Error during user registration: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, data={"message": "Internal Server Error during registration."})

def login_user_view(request: Request, user_manager: UserManager, jwt_auth: JWTAuth, db_session: Session, app_session: AppSession) -> Response:
    """
    Handles user login requests.
    Expects JSON body with 'identifier' (username or email) and 'password'.
    Issues a JWT token upon successful login and sets session data.
    """
    logger.info(f"Received login request for path: {request.path}")
    if request.method != "POST":
        logger.warning(f"Invalid method for /auth/login: {request.method}")
        return JSONResponse(status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, data={"message":  "Method Not Allowed"})

    try:
        data: Optional[Dict[str, Any]] = request.parsed_body
        if not data:
            logger.warning("Login request with no JSON body.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "JSON body is required."})

        identifier = data.get('identifier')
        password = data.get('password')

        if not all([identifier, password]):
            logger.warning("Missing identifier or password for login.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "Identifier (username or email) and password are required."})

        user = user_manager.authenticate_user(db_session, identifier, password)

        if user:
            if not user.is_active:
                logger.warning(f"Login attempt by inactive user: {user.username}.")
                app_session.set_flash("Your account is inactive. Please contact support.", "warning")
                return JSONResponse(status_code=HTTPStatus.FORBIDDEN.value, data ={"message": "Account is inactive."})
            
            if not user.is_email_verified:
                logger.warning(f"Login attempt by unverified user: {user.username}. Prompting for verification.")
                app_session.set_flash("Please verify your email address to activate your account.", "warning")
                return JSONResponse(status_code=HTTPStatus.FORBIDDEN.value, data ={"message": "Email not verified."})

            app_session['user_id'] = user.id
            app_session['user_type'] = user.user_type
            app_session['username'] = user.username

            token_payload = {
                "user_id": user.id,
                "user_type": user.user_type,
                "username": user.username
            }
            jwt_token = jwt_auth.create_access_token(token_payload)

            logger.info(f"User '{user.username}' logged in successfully via session and JWT issued.")
            app_session.set_flash(f"Welcome back, {user.username}!", "success")
            db_session.commit()
            return JSONResponse(status_code=HTTPStatus.OK.value, data ={
                "message": "Login successful",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "access_token": jwt_token
            })
        else:
            logger.warning(f"Failed login attempt for identifier: {identifier}.")
            app_session.set_flash("Invalid username/email or password.", "error")
            return JSONResponse(status_code=HTTPStatus.UNAUTHORIZED.value, data ={"message": "Invalid credentials."})

    except ValidationError as e:
        logger.warning(f"Validation error during user login: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": str(e)})
    except Exception as e:
        logger.exception(f"Error during user login: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, data={"message":  "Internal Server Error during login."})

def verify_email_view(request: Request, user_manager: UserManager, db_session: Session, app_session: AppSession) -> Response:
    """
    Handles email verification requests via a token in the URL query parameters.
    Expected URL: /auth/verify-email?token=<verification_token>
    """
    logger.info(f"Received email verification request for path: {request.path}")
    if request.method != "GET":
        logger.warning(f"Invalid method for /auth/verify-email: {request.method}")
        return JSONResponse(status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, data={"message":  "Method Not Allowed"})

    verification_token = request.query_params.get('token')

    if not verification_token:
        logger.warning("Email verification request missing token parameter.")
        app_session.set_flash("Verification link is invalid or incomplete.", "error")
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": "Verification token is missing."})
    try:
        user = user_manager.verify_user_email(db_session, verification_token)
        if user:
            db_session.commit()
            logger.info(f"Email successfully verified with token: {verification_token[:10]}... for user '{user.username}'.")
            app_session.set_flash("Your email has been successfully verified! You can now log in.", "success")
            return JSONResponse(status_code=HTTPStatus.OK.value, data ={"message": "Email verified successfully."})
        else:
            db_session.rollback()
            logger.warning(f"Email verification failed for token: {verification_token[:10]}... (User not found or verification failed internally).")
            app_session.set_flash("Email confirmation failed. Perhaps the link is invalid or expired.", "error")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": "Email verification failed: Invalid or expired token."})

    except ValidationError as e:
        logger.warning(f"Validation error during email verification: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": str(e)})
    except Exception as e:
        logger.exception(f"Error during email verification: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, data={"message":  "Internal Server Error during email verification."})


def request_password_reset_view(request: Request, user_manager: UserManager, db_session: Session, app_session: AppSession) -> Response:
    """
    Handles requests to initiate password reset.
    Expects JSON body with 'email'.
    """
    logger.info(f"Received password reset request for path: {request.path}")
    if request.method != "POST":
        logger.warning(f"Invalid method for /auth/request-reset-password: {request.method}")
        return JSONResponse(status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, data={"message":  "Method Not Allowed"})

    try:
        data: Optional[Dict[str, Any]] = request.parsed_body
        if not data or 'email' not in data:
            logger.warning("Password reset request missing email in JSON body.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "Email is required in the request body."})

        email = data['email']
        
        success = user_manager.reset_password_request(db_session, email)

        if success:
            db_session.commit()
            logger.info(f"Password reset email initiated for: {email}.")
            app_session.set_flash("If an account with that email exists, a password reset link has been sent.", "info")
            return JSONResponse(status_code=HTTPStatus.OK.value, data ={"message": "If an account with that email exists, a password reset link has been sent."})
        else:
            db_session.rollback()
            logger.warning(f"Password reset request failed for {email}. Responding generically.")
            app_session.set_flash("Could not process your request. Please try again.", "error")
            return JSONResponse(status_code=HTTPStatus.OK.value, data ={"message": "If an account with that email exists, a password reset link has been sent."})

    except ValidationError as e:
        logger.warning(f"Validation error during password reset request: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": str(e)})
    except Exception as e:
        logger.exception(f"Error during password reset request: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, data={"message":  "Internal Server Error during password reset request."})


def reset_password_view(request: Request, user_manager: UserManager, db_session: Session, app_session: AppSession) -> Response:
    """
    Handles the actual password reset.
    Expects JSON body with 'token', 'new_password'.
    """
    logger.info(f"Received password reset attempt for path: {request.path}")
    if request.method != "POST":
        logger.warning(f"Invalid method for /auth/reset-password: {request.method}")
        return JSONResponse(status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, data={"message":  "Method Not Allowed"})

    try:
        data: Optional[Dict[str, Any]] = request.parsed_body
        if not data:
            logger.warning("Password reset request with no JSON body.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "JSON body is required."})

        token = data.get('token')
        new_password = data.get('new_password')

        if not all([token, new_password]):
            logger.warning("Missing token or new_password for password reset.")
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data={"message":  "Token and new password are required."})

        success = user_manager.reset_password(db_session, token, new_password)

        if success:
            db_session.commit()
            logger.info(f"Password successfully reset with token: {token[:10]}...")
            app_session.set_flash("Your password has been successfully reset. You can now log in with your new password.", "success")
            return JSONResponse(status_code=HTTPStatus.OK.value, data ={"message": "Password reset successfully."})
        else:
            db_session.rollback()
            logger.warning(f"Password reset failed for token: {token[:10]}.... Responding generically.")
            app_session.set_flash("Password reset failed. Perhaps the link is invalid or expired.", "error") 
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": "Password reset failed: Invalid or expired token."})

    except ValidationError as e:
        logger.warning(f"Validation error during password reset: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST.value, data ={"message": str(e)})
    except Exception as e:
        logger.exception(f"Error during password reset: {e}")
        db_session.rollback()
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, data={"message":  "Internal Server Error during password reset."})
