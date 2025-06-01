from lback.forms.forms import Form
from lback.forms.fields import CharField, EmailField
from lback. forms.validation import ValidationError
from lback.forms.widgets import TextInput, PasswordInput

class RegisterForm(Form):
    """
    Form for user registration.
    """
    username = CharField(
        max_length=150,
        label="Username",
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        required=True
    )
    email = EmailField(
        label="Email address",
        help_text="A valid email address is required for registration and password resets.",
        required=True
    )
    password = CharField(
        widget=PasswordInput(),
        label="Password",
        help_text="Minimum 8 characters. Must contain at least one uppercase letter, one lowercase letter, one number, and one special character.",
        required=True
    )
    password_confirm = CharField(
        widget=PasswordInput(),
        label="Confirm Password",
        help_text="Re-enter your password to confirm.",
        required=True
    )

    def clean(self):
        """
        Custom validation for password confirmation.
        """
        password = self._cleaned_data.get('password')
        password_confirm = self._cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', ValidationError("Passwords do not match.", code='password_mismatch'))
            self.add_error('password', ValidationError("Passwords do not match.", code='password_mismatch'))

        if password:
            if len(password) < 8:
                self.add_error('password', ValidationError("Password must be at least 8 characters long.", code='password_too_short'))
            if not any(char.isupper() for char in password):
                self.add_error('password', ValidationError("Password must contain at least one uppercase letter.", code='password_no_uppercase'))
            if not any(char.islower() for char in password):
                self.add_error('password', ValidationError("Password must contain at least one lowercase letter.", code='password_no_lowercase'))
            if not any(char.isdigit() for char in password):
                self.add_error('password', ValidationError("Password must contain at least one digit.", code='password_no_digit'))
            if not any(not char.isalnum() for char in password):
                self.add_error('password', ValidationError("Password must contain at least one special character.", code='password_no_special'))

        return self._cleaned_data

class LoginForm(Form):
    """
    Form for user login.
    """
    identifier = CharField(
        label="Username or Email",
        help_text="Enter your username or email address."
    )
    password = CharField(
        widget=PasswordInput(),
        label="Password"
    )

class RequestPasswordResetForm(Form):
    """
    Form for requesting a password reset email.
    """
    email = EmailField(
        label="Email address",
        help_text="Enter the email address associated with your account."
    )

class SetNewPasswordForm(Form):
    """
    Form for setting a new password after a reset request.
    Requires a 'token' field, usually hidden or pre-filled.
    """
    token = CharField(
        required=True,
        label="Reset Token",
        help_text="This token is provided in the reset link.",
        widget=TextInput(attrs={'readonly': 'readonly'})
    )
    new_password = CharField(
        widget=PasswordInput(),
        label="New Password",
        help_text="Minimum 8 characters. Must contain at least one uppercase letter, one lowercase letter, one number, and one special character."
    )
    confirm_new_password = CharField(
        widget=PasswordInput(),
        label="Confirm New Password",
        help_text="Re-enter your new password to confirm."
    )

    def clean(self):
        if not hasattr(self, 'cleaned_data') or self.cleaned_data is None:
            self.cleaned_data = {}

        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        token = self.cleaned_data.get('token')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.") 

        return self.cleaned_data