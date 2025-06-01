Email Sending in Lback Framework
================================

Lback provides a dedicated utility for sending emails, encapsulated within the ``EmailSender`` class. This class is designed to be configurable and flexible, allowing you to integrate email functionalities like account verification, password resets, and general notifications into your application.

---

1. The ``EmailSender`` Class
----------------------------

The ``EmailSender`` class (located in your project's utilities, e.g., ``lback/utils/email_sender.py``) is responsible for handling all aspects of sending emails via an SMTP server. It leverages Python's built-in ``smtplib`` and ``email.mime`` modules.

**Key Features:**

* **Configurable SMTP Settings**: All SMTP server details (host, port, credentials, TLS) are provided during initialization, making the sender reusable.
* **HTML and Plain Text Support**: Easily send emails in either plain text or rich HTML format.
* **Dedicated Methods**: Includes convenience methods for common email types like verification and password reset emails, which generate pre-formatted HTML bodies.
* **Robust Error Logging**: Comprehensive logging helps diagnose any issues during email transmission.

**Initialization Parameters:**

The ``EmailSender`` is initialized with the following parameters:

* **smtp_server** (str): The address of your SMTP server (e.g., ``'smtp.mailprovider.com'``).
* **smtp_port** (int): The port number for your SMTP server (commonly ``587`` for TLS or ``465`` for SSL).
* **smtp_username** (str): The username for SMTP authentication.
* **smtp_password** (str): The password for SMTP authentication.
* **sender_email** (str): The email address that will appear as the sender.
* **use_tls** (bool, *default: True*): Whether to enable Transport Layer Security (TLS) for a secure connection. Highly recommended.
* **sender_name** (str, *default: "Your App Name"*): The display name that will appear as the sender (e.g., "Lback App Support").

---

2. Email Configuration in ``settings.py``
---------------------------------------

To integrate email sending into your Lback application, you should define your SMTP server settings in your ``settings.py`` file. This allows for easy management and separation of sensitive credentials from your code.

**Example** ``settings.py`` **Email Settings:**

.. code-block:: python

    SMTP_SERVER = "smtp.example.com"  # Example: "smtp.gmail.com" for Gmail
    SMTP_PORT = 587
    EMAIL_USERNAME = "your_app_email@example.com" # Example: "app.notifications@example.com".
    EMAIL_PASSWORD = "your_email_app_password" # Example: "abcd efgh ijkl mnop" (for app passwords)
    SENDER_EMAIL = "no-reply@your-domain.com" # Example: "noreply@example.com"
    USE_TLS = True
    SENDER_NAME = "Your Application" # Example: "MyProject Notifications"

**Note:** It's a best practice to load sensitive information like passwords from environment variables (e.g., using ``os.environ.get()``) rather than hardcoding them directly in ``settings.py``.

---

3. Using the ``EmailSender`` in Views (or other modules)
--------------------------------------------------------

The ``EmailSender`` object needs to be initialized with your configuration. This is typically done once when your application starts up, and then the instance is made available where needed (e.g., passed to views, or accessed via a global application context).

**Example View: Sending a Password Reset Email**

Let's say you have a password reset functionality where you generate a unique token and send a link to the user's email.

.. code-block:: python

    # In your views/auth.py or similar file
    from lback.core.types import Request
    from lback.core.config import Config
    from lback.utils.email_sender import EmailSender # Assuming you put EmailSender in utils/email_sender.py
    from lback.core.response import Response
    from lback.utils.db_session import get_db_session # Assuming you have a way to get db_session
    from lback.utils.shortcuts import render, redirect
    # from your_app.models import User, PasswordResetToken # Example models

    import uuid
    from datetime import datetime, timedelta

    def forgot_password_view(request: Request) -> Response:
        db_session = get_db_session(request) # Get DB session from request context

        if request.method == 'POST':
            email = request.form.get('email')
            if not email:
                request.session['flash_messages'].append({'message': 'Please enter your email address.', 'category': 'error'})
                return redirect('/forgot-password')

            user = db_session.query(User).filter_by(email=email).first()
            if not user:
                # To prevent email enumeration, always respond as if email was sent
                request.session['flash_messages'].append({'message': 'If an account with that email exists, a password reset link has been sent.', 'category': 'info'})
                return redirect('/forgot-password')

            # Generate a unique token
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1) # Link valid for 1 hour

            # Save the token to the database (associate with user)
            new_reset_token = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
            db_session.add(new_reset_token)
            db_session.commit()

            # Construct the reset link (replace with your actual domain and route)
            reset_link = f"{request.base_url_no_path}/reset-password?token={token}"

            # Instantiate EmailSender with your config (in a real app, this might be a singleton)
            app_config = Config() # Load config for demonstration
            email_sender = EmailSender(
                smtp_server=app_config.SMTP_SERVER,
                smtp_port=app_config.SMTP_PORT,
                smtp_username=app_config.SMTP_USERNAME,
                smtp_password=app_config.SMTP_PASSWORD,
                sender_email=app_config.SENDER_EMAIL,
                use_tls=app_config.USE_TLS,
                sender_name=app_config.SENDER_NAME
            )

            # Send the email
            if email_sender.send_password_reset_email(user.email, user.username, reset_link):
                request.session['flash_messages'].append({'message': 'A password reset link has been sent to your email.', 'category': 'success'})
            else:
                request.session['flash_messages'].append({'message': 'Failed to send password reset email. Please try again later.', 'category': 'error'})

            return redirect('/forgot-password')

        return render_template('forgot_password.html', request=request)

    def contact_us_view(request: Request) -> Response:
        db_session = get_db_session(request)

        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')

            # Basic validation
            if not all([name, email, subject, message]):
                request.session['flash_messages'].append({'message': 'All fields are required.', 'category': 'error'})
                return redirect('/contact-us')

            # Instantiate EmailSender
            app_config = Config()
            email_sender = EmailSender(
                smtp_server=app_config.SMTP_SERVER,
                smtp_port=app_config.SMTP_PORT,
                smtp_username=app_config.SMTP_USERNAME,
                smtp_password=app_config.SMTP_PASSWORD,
                sender_email=app_config.SENDER_EMAIL,
                use_tls=app_config.USE_TLS,
                sender_name=app_config.SENDER_NAME
            )

            # Define the recipient (e.g., your admin email)
            admin_email = app_config.ADMIN_EMAIL # Make sure you have this in your config

            email_body = f"""
            New Contact Form Submission:
            Name: {name}
            Email: {email}
            Subject: {subject}
            Message:
            {message}
            """

            if email_sender.send_generic_email(admin_email, f"Contact Form: {subject}", email_body, is_html=False):
                request.session['flash_messages'].append({'message': 'Your message has been sent successfully!', 'category': 'success'})
            else:
                request.session['flash_messages'].append({'message': 'Failed to send your message. Please try again later.', 'category': 'error'})

            return redirect('/contact-us')

        return render_template('contact_us.html', request=request)


**Important Considerations:**

* **Asynchronous Sending**: For production applications, sending emails synchronously within a web request can block the response and degrade user experience. Consider implementing an asynchronous task queue (e.g., Celery, RQ) to send emails in the background.
* **Error Handling**: The ``send_email`` method returns ``True`` on success and ``False`` on failure. Always check this return value and provide appropriate feedback to the user.
* **Templating**: For more complex email bodies, especially HTML emails, you might want to use a dedicated templating engine (like Jinja2) to render your email content before passing it to ``EmailSender``.

---

By leveraging the ``EmailSender`` class and its configuration, you can robustly integrate email communication into your Lback applications.