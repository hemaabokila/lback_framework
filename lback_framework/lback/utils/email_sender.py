import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Utility class for sending emails.
    Configured to use parameters passed during initialization for security and flexibility.
    """
    def __init__(self, smtp_server: str, smtp_port: int, smtp_username: str, smtp_password: str, sender_email: str, use_tls: bool = True, sender_name: str = "Your App Name"):
        """
        Initializes the EmailSender with SMTP configuration.

        Args:
            smtp_server: The SMTP server address (e.g., 'smtp.example.com').
            smtp_port: The SMTP server port (e.g., 587).
            smtp_username: The username for SMTP authentication.
            smtp_password: The password for SMTP authentication.
            sender_email: The email address to use as the sender.
            use_tls: Boolean indicating whether to use TLS encryption (default is True).
            sender_name: The name to display as the sender (default is "Your App Name").
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.sender_email = sender_email
        self.use_tls = use_tls
        self.sender_name = sender_name
        
        logger.info("EmailSender initialized with provided SMTP settings.")

    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False):
        """
        Internal method to handle the actual email sending process.
        Uses instance attributes for SMTP configuration.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            if is_html:
                part1 = MIMEText(body, 'html')
                msg.attach(part1)
            else:
                part1 = MIMEText(body, 'plain')
                msg.attach(part1)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email} with subject: '{subject}'")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} with subject '{subject}': {e}", exc_info=True)
            return False

    def send_verification_email(self, to_email: str, username: str, verification_link: str) -> bool:
        """
        Sends an email verification link to a new user.
        """
        subject = "Please Verify Your Email Address"
        html_body = f"""\
        <html>
        <body>
            <p>Hello {username},</p>
            <p>Thank you for registering with {self.sender_name}! To complete your registration and activate your account, please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}">Verify My Email Address</a></p>
            <p>If you did not register for an account, please ignore this email.</p>
            <p>Regards,<br>{self.sender_name} Team</p>
        </body>
        </html>
        """
        return self._send_email(to_email, subject, html_body, is_html=True)

    def send_password_reset_email(self, to_email: str, username: str, reset_link: str) -> bool:
        """
        Sends a password reset link to a user.
        """
        subject = "Password Reset Request"
        html_body = f"""\
        <html>
        <body>
            <p>Hello {username},</p>
            <p>You have requested to reset your password for your account with {self.sender_name}.</p>
            <p>Please click on the link below to reset your password:</p>
            <p><a href="{reset_link}">Reset My Password</a></p>
            <p>This link will expire in 1 hour. If you did not request a password reset, please ignore this email.</p>
            <p>Regards,<br>{self.sender_name} Team</p>
        </body>
        </html>
        """
        return self._send_email(to_email, subject, html_body, is_html=True)

    def send_generic_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Sends a generic email (plain text or HTML).
        """
        return self._send_email(to_email, subject, body, is_html)
