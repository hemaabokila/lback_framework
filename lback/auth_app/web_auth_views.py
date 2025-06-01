import logging
from http import HTTPStatus

from .auth_forms import RegisterForm, LoginForm, RequestPasswordResetForm, SetNewPasswordForm

from lback.core.response import Response
from lback.core.types import Request, HTTPMethod
from lback.utils.shortcuts import render, redirect, return_500
from lback.forms.validation import ValidationError

logger = logging.getLogger(__name__)


def show_register_page(request: Request) -> Response:
    """
    Renders the user registration form page.
    """
    logger.info(f"Displaying registration page for path: {request.path}")

    app_session = request.session
    if app_session is None:
        logger.error("AppSession is not available on the request for show_register_page.")
        return return_500(request, message="Session service unavailable.")
    form = RegisterForm()

    csrf_token_value = app_session.get('_csrf_token')
    if not csrf_token_value:
        logger.warning("CSRF token not found in session for show_register_page. "
                       "Ensure CSRFMiddleware is correctly configured and positioned.")

    context = {
        "flash_messages": app_session.get_flashed_messages(),
        "csrf_token": csrf_token_value,
        "form": form
    }
    return render(request, "register.html", context)


def handle_register_submit(request: Request) -> Response:
    """
    Handles the submission of the new user registration form (POST request).
    """
    logger.info(f"Received registration form submission for path: {request.path}")

    user_manager = request.user_manager
    db_session = request.db_session
    app_session = request.session

    if user_manager is None or db_session is None or app_session is None:
        logger.critical("Missing core dependencies (user_manager, db_session, app_session) in handle_register_submit.")
        app_session.set_flash("An internal server error occurred due to missing dependencies.", "danger")
        return return_500(request, message="Internal Server Error: Core dependencies missing.")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Invalid method for web /auth/register: {request.method}. Expected POST.")
        app_session.set_flash("Invalid request method.", "error")
        return redirect("/register/", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value)

    form = RegisterForm(data=request.POST)

    try:
        if form.is_valid():
            cleaned_data = form.cleaned_data
            username = cleaned_data['username']
            email = cleaned_data['email']
            password = cleaned_data['password']
            logger.debug(f"handle_register_submit: Attempting to register user with email: {email}")
            user = user_manager.register_user(db_session, username, email, password)

            if user:
                logger.info(f"handle_register_submit: User '{username}' registered successfully. Committing DB session.")
                db_session.commit()
                app_session.set_flash("Registration successful! Please check your email to activate your account.", "success")
                logger.info(f"User '{username}' registered successfully via web form. Redirecting to /login.")
                return redirect("/login/")
            else:
                logger.warning(f"handle_register_submit: user_manager.register_user returned None/False for user: {username}.")
                app_session.set_flash("Registration failed. Please check your input or try again later.", "error")
                logger.error(f"Failed to register user '{username}' via web form. Redirecting to /register.")
                return redirect("/register/")

        else:
            logger.warning(f"Registration form validation failed. Errors: {form.errors}")
            app_session.set_flash("Please correct the errors below.", "error")
            context = {
                "flash_messages": app_session.get_flashed_messages(),
                "csrf_token": app_session.get('_csrf_token'),
                "form": form
            }
            return render(request, "register.html", context, status_code=HTTPStatus.BAD_REQUEST.value)

    except ValidationError as e:
        logger.warning(f"Validation error during web user registration process. Error: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash(str(e), "error")
        return redirect("/register/")

    except ValueError as e:
        logger.critical(f"Critical error during web user registration process: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash("An internal server error occurred. Please contact support. (Missing default user group)", "danger")
        return return_500(request, exception=e)
    except Exception as e:
        logger.exception(f"Critical error during web user registration process. Exception: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash("An internal error occurred during registration. Please try again later.", "danger")
        return return_500(request, exception=e)


def show_login_page(request: Request) -> Response:
    """
    Renders the user login form page.
    """
    logger.info(f"Displaying login page for path: {request.path}")

    app_session = request.session
    if app_session is None:
        logger.error("AppSession is not available on the request for show_login_page.")
        return return_500(request, message="Session service unavailable.")

    form = LoginForm()

    csrf_token_value = app_session.get('_csrf_token')
    logger.debug(f"CSRF token being passed to login.html template: {csrf_token_value}")

    context = {
        "flash_messages": app_session.get_flashed_messages(),
        "csrf_token": csrf_token_value,
        "form": form
    }
    return render(request, "auth_login", context)


def handle_login_submit(request: Request) -> Response:
    """
    Handles the submission of the user login form (POST request).
    """
    logger.info(f"Received login form submission for path: {request.path}")

    user_manager = request.user_manager
    db_session = request.db_session
    app_session = request.session

    if user_manager is None or db_session is None or app_session is None:
        logger.critical("Missing core dependencies (user_manager, db_session, app_session) in handle_login_submit.")
        app_session.set_flash("An internal server error occurred due to missing dependencies.", "danger")
        return return_500(request, message="Internal Server Error: Core dependencies missing.")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Invalid method for web /auth/login: {request.method}. Expected POST.")
        app_session.set_flash("Invalid request method.", "error")
        return redirect("/login/", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value)

    form = LoginForm(data=request.POST)

    try:
        if form.is_valid():
            cleaned_data = form.cleaned_data
            identifier = cleaned_data['identifier']
            password = cleaned_data['password']

            user = user_manager.authenticate_user(db_session, identifier, password)

            if user:
                if not user.is_active:
                    logger.warning(f"Web login attempt by inactive user: {user.username}.")
                    app_session.set_flash("Your account is inactive. Please contact support.", "warning")
                    if db_session.is_active:
                        db_session.rollback()
                    return redirect("/login/", status_code=HTTPStatus.FORBIDDEN.value)

                if not user.is_email_verified:
                    logger.warning(f"Web login attempt by unverified user: {user.username}. Prompting for verification.")
                    app_session.set_flash("Please verify your email to activate your account.", "warning")
                    if db_session.is_active:
                        db_session.rollback()
                    return redirect("/login/", status_code=HTTPStatus.FORBIDDEN.value)

                app_session['user_id'] = user.id
                app_session['user_type'] = user.user_type
                app_session['username'] = user.username

                app_session.set_flash(f"Welcome, {user.username}!", "success")
                db_session.commit()
                logger.info(f"User '{user.username}' logged in successfully via web form. Redirecting to /dashboard.")
                return redirect("/")

            else:
                logger.warning(f"handle_login_submit: Failed web login attempt for identifier: {identifier}. Invalid credentials.")
                app_session.set_flash("Invalid username/email or password.", "error")
                if db_session.is_active:
                    db_session.rollback()
                context = {
                    "flash_messages": app_session.get_flashed_messages(),
                    "csrf_token": app_session.get('_csrf_token'),
                    "form": form
                }
                return render(request, "auth_login", context, status_code=HTTPStatus.UNAUTHORIZED.value)

        else:
            logger.warning(f"Login form validation failed. Errors: {form.errors}")
            app_session.set_flash("Please correct the errors below.", "error")
            context = {
                "flash_messages": app_session.get_flashed_messages(),
                "csrf_token": app_session.get('_csrf_token'),
                "form": form
            }
            return render(request, "auth_login", context, status_code=HTTPStatus.BAD_REQUEST.value)

    except ValidationError as e:
        logger.warning(f"Validation error during web login process. Error: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash(str(e), "error")
        return redirect("/login/")

    except Exception as e:
        logger.exception(f"Critical error during web login process. Exception: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash("An unexpected error occurred during login. Please try again later.", "danger")
        return return_500(request, exception=e)


def show_request_password_reset_page(request: Request) -> Response:
    """
    Renders the page for requesting a password reset email.
    """
    logger.info(f"Displaying request password reset page for path: {request.path}")

    app_session = request.session
    if app_session is None:
        logger.error("AppSession is not available on the request for show_request_password_reset_page.")
        return return_500(request, message="Session service unavailable.")

    form = RequestPasswordResetForm()

    csrf_token_value = app_session.get('_csrf_token')
    logger.debug(f"CSRF token being passed to request_password_reset.html template: {csrf_token_value}")

    context = {
        "flash_messages": app_session.get_flashed_messages(),
        "csrf_token": csrf_token_value,
        "form": form
    }
    return render(request, "request_password_reset.html", context)


def handle_request_password_reset_submit(request: Request) -> Response:
    """
    Handles the submission of the password reset request form (POST request).
    """
    logger.info(f"Received web password reset request for path: {request.path}")

    user_manager = request.user_manager
    db_session = request.db_session
    app_session = request.session

    if user_manager is None or db_session is None or app_session is None:
        logger.critical("Missing core dependencies in handle_request_password_reset_submit.")
        app_session.set_flash("An internal server error occurred due to missing dependencies.", "danger")
        return return_500(request, message="Internal Server Error: Core dependencies missing.")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Invalid method for web /auth/request-reset-password: {request.method}. Expected POST.")
        app_session.set_flash("Invalid request method.", "error")
        return redirect("/request-reset-password/", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value)

    form = RequestPasswordResetForm(data=request.POST)

    try:
        if form.is_valid():
            email = form.cleaned_data['email']
            logger.debug(f"handle_request_password_reset_submit: Received email: {email}")
            web_reset_password_confirm_path = "/reset-password-confirm/"
            success = user_manager.reset_password_request(db_session, email, reset_url_path=web_reset_password_confirm_path)
            logger.info(f"Password reset email initiated for: {email} via web form. Success: {success}")
            app_session.set_flash("If an account with that email exists, a password reset link has been sent.", "info")
            db_session.commit()
            return redirect("/request-reset-password/")
        else:
            logger.warning(f"Request password reset form validation failed. Errors: {form.errors}")
            app_session.set_flash("Please correct the errors below.", "error")
            context = {
                "flash_messages": app_session.get_flashed_messages(),
                "csrf_token": app_session.get('_csrf_token'),
                "form": form
            }
            return render(request, "request_password_reset.html", context, status_code=HTTPStatus.BAD_REQUEST.value)

    except ValidationError as e:
        logger.warning(f"Validation error during web password reset request. Error: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash(str(e), "error")
        return redirect("/request-reset-password/")

    except Exception as e:
        logger.exception(f"Critical error during web password reset request. Exception: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash("An internal error occurred. Please try again later.", "danger")
        return return_500(request, exception=e)

def show_reset_password_confirm_page(request: Request) -> Response:
    """
    Renders the page for confirming a password reset.
    """
    logger.info(f"Displaying reset password confirm page for path: {request.path}")

    app_session = request.session
    if app_session is None:
        logger.error("AppSession is not available on the request for show_reset_password_confirm_page.")
        return return_500(request, message="Session service unavailable.")

    reset_token = request.query_params.get('token', '')
    form = SetNewPasswordForm(initial={'token': reset_token})

    csrf_token_value = app_session.get('_csrf_token')

    context = {
        "flash_messages": app_session.get_flashed_messages(),
        "csrf_token": csrf_token_value,
        "form": form,
        "reset_token": reset_token
    }
    return render(request, "reset_password_confirm.html", context)


def handle_reset_password_confirm_submit(request: Request) -> Response:
    """
    Handles the submission of the password reset confirmation form (POST request).
    """
    logger.info(f"Received web password reset confirmation for path: {request.path}")

    user_manager = request.user_manager
    db_session = request.db_session
    app_session = request.session

    if user_manager is None or db_session is None or app_session is None:
        logger.critical("Missing core dependencies in handle_reset_password_confirm_submit.")
        app_session.set_flash("An internal server error occurred due0 to missing dependencies.", "danger")
        return return_500(request, message="Internal Server Error: Core dependencies missing.")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Invalid method for web /auth/reset-password: {request.method}. Expected POST.")
        app_session.set_flash("Invalid request method.", "error")
        return redirect("/login", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value)

    form = SetNewPasswordForm(data=request.POST)

    try:
        if form.is_valid():
            cleaned_data = form.cleaned_data
            token = cleaned_data['token']
            new_password = cleaned_data['new_password']

            logger.debug(f"handle_reset_password_confirm_submit: Received token (from form): {token[:10] if token else 'None'}..., password_present={bool(new_password)}")

            success = user_manager.reset_password(db_session, token, new_password)

            if success:
                db_session.commit()
                logger.info(f"Password successfully reset with token: {token[:10]}... via web form.")
                app_session.set_flash("Your password has been reset successfully. You can now log in with your new password.", "success")
                return redirect("/login/")
            else:
                logger.warning(f"Web password reset failed for token: {token[:10]}....")
                if db_session.is_active:
                    db_session.rollback()
                app_session.set_flash("Password reset failed. Perhaps the link is invalid or expired.", "error")
                return redirect(f"/reset-password-confirm/?token={token or ''}/")
        else:
            logger.warning(f"Set new password form validation failed. Errors: {form.errors}")
            app_session.set_flash("Please correct the errors below.", "error")
            context = {
                "flash_messages": app_session.get_flashed_messages(),
                "csrf_token": app_session.get('_csrf_token'),
                "form": form
            }
            return render(request, "reset_password_confirm.html", context, status_code=HTTPStatus.BAD_REQUEST.value)

    except ValidationError as e:
        logger.warning(f"Validation error during web password reset confirmation. Error: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash(str(e), "error")
        return redirect(f"/reset-password-confirm/?token={token or ''}/")

    except Exception as e:
        logger.exception(f"Critical error during web password reset confirmation. Exception: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash("An internal error occurred. Please try again later.", "danger")
        return return_500(request, exception=e)

def verify_email_web_view(request: Request) -> Response:
    """
    Handles email verification via a web link (GET request).
    """
    logger.info(f"Received web email verification request for path: {request.path}")

    verification_token = None

    user_manager = request.user_manager
    db_session = request.db_session
    app_session = request.session

    if user_manager is None or db_session is None or app_session is None:
        logger.critical("Missing core dependencies in verify_email_web_view.")
        app_session.set_flash("An internal server error occurred due to missing dependencies.", "danger")
        return return_500(request, message="Internal Server Error: Core dependencies missing.")

    if request.method != HTTPMethod.GET:
        logger.warning(f"Invalid method for web /auth/verify-email: {request.method}. Expected GET.")
        app_session.set_flash("Invalid request method.", "error")
        return redirect("/", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value)

    verification_token = request.query_params.get('token')
    logger.debug(f"verify_email_web_view: Received verification token: {verification_token[:10] if verification_token else 'None'}...")

    if not verification_token:
        logger.warning("Web email verification request missing token parameter.")
        app_session.set_flash("The activation link is invalid or incomplete.", "error")
        if db_session.is_active:
            db_session.rollback()
        return redirect("/login/", status_code=HTTPStatus.BAD_REQUEST.value)

    try:
        user = user_manager.verify_user_email(db_session, verification_token)

        if user:
            db_session.commit()
            logger.info(f"Email successfully verified with token: {verification_token[:10]}... for user '{user.username}' via web.")
            app_session.set_flash("Your email has been successfully confirmed! You can now log in.", "success")
            return redirect("/login/")
        else:
            logger.warning(f"Web email verification failed for token: {verification_token[:10]}... (User not found or verification failed internally).")
            if db_session.is_active:
                db_session.rollback()
            app_session.set_flash("Email confirmation failed. Perhaps the link is invalid or expired.", "error")
            return redirect("/login/")
    except ValidationError as e:
        logger.warning(f"Validation error during web email verification for token: {verification_token[:10] if verification_token else 'None'}... Error: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash(str(e), "error")
        return redirect("/login/")

    except Exception as e:
        logger.exception(f"Critical error during web email verification for token: {verification_token[:10] if verification_token else 'None'}... Exception: {e}")
        if db_session and db_session.is_active:
            db_session.rollback()
        app_session.set_flash("An internal error occurred during email confirmation. Please try again later.", "danger")
        return return_500(request, exception=e)


def logout_user_view(request: Request) -> Response:
    """
    Logs out the current user by clearing their session data.
    """
    logger.info(f"Received logout request for path: {request.path}")

    app_session = request.session
    if app_session is None:
        logger.warning("AppSession is not available on the request for logout_user_view. Cannot perform logout.")
        return redirect("/login/")

    app_session.clear()
    app_session.set_flash("You have been successfully logged out.", "success")
    logger.info("User logged out successfully. Redirecting to /login.")
    return redirect("/login/")