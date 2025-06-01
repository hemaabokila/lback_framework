import logging
import re
import os
from typing import Any, Dict, Optional, List, Type, Callable, Tuple

from .widgets import Widget, TextInput, CheckboxInput, Select, FileInput
from .validation import ValidationError

logger = logging.getLogger(__name__)

class Field:
    """
    Base class for all form fields.
    Fields manage data validation and rendering using a widget.
    """
    widget: Type[Widget] = TextInput

    def __init__(
        self,
        required: bool = True,
        label: Optional[str] = None,
        initial: Any = None,
        widget: Optional[Widget] = None,
        attrs: Optional[Dict[str, Any]] = None,
        help_text: Optional[str] = None,
        error_messages: Optional[Dict[str, str]] = None,
        validators: Optional[List[Callable[[Any], None]]] = None
    ):
        """
        Initializes a form field.

        Args:
            required: If True, the field is required. Defaults to True.
            label: The label for the field in the form. If None, a label will be generated.
            initial: The initial value of the field when the form is displayed.
            widget: The widget instance to use for rendering. Defaults to an instance of self.widget.
            attrs: A dictionary of HTML attributes for the widget.
            help_text: Optional help text for the field.
            error_messages: A dictionary of custom error messages for validation errors.
            validators: A list of validator functions to run after basic field validation.
                        Each validator function should accept one argument (the cleaned value)
                        and raise ValidationError if validation fails.
        """
        self.required = required
        self.label = label
        self.initial = initial
        self.widget = widget if widget is not None else self.widget(attrs=attrs)
        self.attrs = attrs if attrs is not None else {}
        self.help_text = help_text
        self.error_messages = {
            'required': 'This field is required.',
            'invalid': 'Enter a valid value.',
        }
        if error_messages:
            self.error_messages.update(error_messages)

        self.validators = validators if validators is not None else []

        self.name: Optional[str] = None
        self.value: Any = None
        self.cleaned_value: Any = None
        self.errors: List[ValidationError] = []

        self.is_bound = False

    def bind(self, name: str, data: Dict[str, Any], files: Dict[str, Any]):
        """
        Binds the field to data from the request.
        Called by the Form when data is submitted.

        Args:
            name: The name of the field (from the form definition).
            data: The dictionary of data (e.g., request.POST).
            files: The dictionary of files (e.g., request.FILES).
        """
        self.name = name
        self.is_bound = True
        self.value = self.widget.value_from_datadict(data, files, name)
        logger.debug(f"Field '{self.name}': Bound with raw value: {repr(self.value)}")


    def is_valid(self) -> bool:
        """
        Validates the field's data.
        Returns True if the field is valid, False otherwise.
        Validation errors are stored in self.errors.
        """
        self.errors = []


        if self.required and (self.value is None or (isinstance(self.value, str) and self.value.strip() == '' and not isinstance(self, FileField))):
             if isinstance(self, FileField) and self.value is None:
                  self.errors.append(ValidationError(self.error_messages['required'], code='required'))
                  logger.debug(f"Field '{self.name}': Validation failed - Required FileField is missing.")
                  return False

             if not isinstance(self, FileField) and (self.value is None or (isinstance(self.value, str) and self.value.strip() == '')):
                 self.errors.append(ValidationError(self.error_messages['required'], code='required'))
                 logger.debug(f"Field '{self.name}': Validation failed - Required field is missing/empty.")
                 return False

        try:
            self.cleaned_value = self.to_python(self.value)
            logger.debug(f"Field '{self.name}': to_python successful. Cleaned value: {repr(self.cleaned_value)}")

            if not self.errors:
                for validator in self.validators:
                    try:
                        validator(self.cleaned_value)
                        logger.debug(f"Field '{self.name}': Custom validator {getattr(validator, '__name__', str(validator))} passed.")
                    except ValidationError as e:
                        self.errors.append(e)
                        logger.debug(f"Field '{self.name}': Custom validator {getattr(validator, '__name__', str(validator))} failed: {e.message}")
                    except Exception as e:
                        logger.exception(f"Field '{self.name}': Unexpected error running custom validator {getattr(validator, '__name__', str(validator))}: {e}")
                        self.errors.append(ValidationError(f"Validator error: {e}", code='validator_error'))


        except ValidationError as e:
            self.errors.append(e)
            logger.debug(f"Field '{self.name}': Validation failed in to_python: {e.message}")
        except Exception as e:
            logger.exception(f"Field '{self.name}': Unexpected error during to_python: {e}")
            self.errors.append(ValidationError(f"Internal error: {e}", code='internal_error'))

        return not bool(self.errors)

    def to_python(self, value: Any) -> Any:
        """
        Converts the raw value from the widget into a Python object.
        This method performs basic type conversion and may raise ValidationError.
        Subclasses must implement this method.

        Args:
            value: The raw value obtained from the widget.

        Returns:
            The converted Python object.

        Raises:
            ValidationError: If the value cannot be converted or is invalid.
        """
        raise NotImplementedError("Subclasses must implement the 'to_python' method.")

    def render(self, value: Any = None, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the field using its widget.

        Args:
            value: The value to render. Defaults to self.value if bound, self.initial if unbound.
                   Explicitly passing a value here overrides the default.
            attrs: Additional HTML attributes for the widget. Merged with self.attrs.

        Returns:
            An HTML string for the field's input element.
        """
        if value is None:
            value_to_render = self.value if self.is_bound else self.initial
        else:
            value_to_render = value

        return self.widget.render(name=self.name, value=value_to_render, attrs=self.attrs)


class CharField(Field):
    """
    A field that handles text input.
    Validates that the input is a string.
    """
    widget = TextInput

    def __init__(
        self,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        strip: bool = True,
        empty_value: str = '',
        **kwargs: Any
    ):
        """
        Initializes a CharField.
        """
        self.max_length = max_length
        self.min_length = min_length
        self.strip = strip
        self.empty_value = empty_value
        super().__init__(**kwargs)

        self.error_messages.update({
            'max_length': 'Ensure this value has at most %(limit_value)d characters (it has %(show_value)d).',
            'min_length': 'Ensure this value has at least %(limit_value)d characters (it has %(show_value)d).',
        })

    def to_python(self, value: Any) -> Optional[str]:
        """
        Converts the input value to a string and performs basic validation.
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return self.empty_value if not self.required else None

        try:
            value = str(value)
        except Exception:
            raise ValidationError(self.error_messages['invalid'], code='invalid')

        if self.strip:
            value = value.strip()

        if value == '' and not self.required:
             return self.empty_value

        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                self.error_messages['max_length'],
                code='max_length',
                params={'limit_value': self.max_length, 'show_value': len(value)}
            )
        if self.min_length is not None and len(value) < self.min_length and value != '':
             raise ValidationError(
                 self.error_messages['min_length'],
                 code='min_length',
                 params={'limit_value': self.min_length, 'show_value': len(value)}
             )

        return value


class IntegerField(Field):
    """
    A field that handles integer input.
    Validates that the input can be converted to an integer.
    """
    widget = TextInput

    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        empty_value: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Initializes an IntegerField.
        """
        self.min_value = min_value
        self.max_value = max_value
        self.empty_value = empty_value
        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid': 'Enter a valid integer.',
            'min_value': 'Ensure this value is greater than or equal to %(limit_value)d.',
            'max_value': 'Ensure this value is less than or equal to %(limit_value)d.',
        })

    def to_python(self, value: Any) -> Optional[int]:
        """
        Converts the input value to an integer and performs validation.
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return self.empty_value if not self.required else None

        try:
            if isinstance(value, str):
                 value = value.strip()
            cleaned_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'], code='invalid')

        if self.min_value is not None and cleaned_value < self.min_value:
            raise ValidationError(
                self.error_messages['min_value'],
                code='min_value',
                params={'limit_value': self.min_value}
            )
        if self.max_value is not None and cleaned_value > self.max_value:
            raise ValidationError(
                self.error_messages['max_value'],
                code='max_value',
                params={'limit_value': self.max_value}
            )

        return cleaned_value


class BooleanField(Field):
    """
    A field that handles boolean input, typically from a checkbox.
    """
    widget = CheckboxInput

    def __init__(
        self,
        required: bool = False,
        initial: bool = False,
        empty_value: bool = False,
        **kwargs: Any
    ):
        """
        Initializes a BooleanField.
        """
        kwargs['required'] = required
        kwargs['initial'] = initial
        self.empty_value = empty_value
        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid': 'Enter a valid boolean value.',
        })

    def to_python(self, value: Any) -> bool:
        """
        Converts the input value to a boolean.
        """
        if isinstance(value, bool):
            return value

        if value is None or (isinstance(value, str) and value.strip() == ''):
             return self.empty_value if not self.required else False

        if isinstance(value, str):
            lower_value = value.strip().lower()
            if lower_value in ('on', '1', 'true', 'yes'):
                return True
            if lower_value in ('0', 'false', 'no'):
                return False

        if isinstance(value, (int, float)):
             return bool(value)

        raise ValidationError(self.error_messages['invalid'], code='invalid')


class EmailField(CharField):
    """
    A field that handles email input.
    Inherits from CharField and adds email format validation.
    """
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self, **kwargs: Any):
        """
        Initializes an EmailField.
        """
        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid': 'Enter a valid email address.',
        })

    def to_python(self, value: Any) -> Optional[str]:
        """
        Converts the input value to a string and validates email format.
        """
        cleaned_value = super().to_python(value)

        if cleaned_value is None or (isinstance(cleaned_value, str) and cleaned_value == ''):
             return cleaned_value

        if not self.EMAIL_REGEX.match(cleaned_value):
            raise ValidationError(self.error_messages['invalid'], code='invalid_email')

        return cleaned_value


class ChoiceField(Field):
    """
    A field that represents a choice from a limited set of options.
    Typically rendered with a Select widget.
    """
    widget = Select

    def __init__(
        self,
        choices: List[Tuple[Any, str]],
        empty_value: Optional[Any] = None,
        **kwargs: Any
    ):
        """
        Initializes a ChoiceField.
        """
        self.choices = choices
        self.empty_value = empty_value

        if 'widget' not in kwargs:
             kwargs['widget'] = Select(choices=choices, attrs=kwargs.get('attrs'))
             kwargs.pop('attrs', None)

        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid_choice': 'Select a valid choice. %(value)s is not one of the available choices.',
        })

        self._valid_values = {str(value) for value, label in choices}


    def to_python(self, value: Any) -> Optional[Any]:
        """
        Validates that the selected value is one of the available choices
        and returns the cleaned value.
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return self.empty_value if not self.required else None

        submitted_value_str = str(value)

        if submitted_value_str not in self._valid_values:
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value}
            )

        cleaned_value = None
        for option_value, _ in self.choices:
             if str(option_value) == submitted_value_str:
                 cleaned_value = option_value
                 break

        if cleaned_value is None:
             logger.warning(f"ChoiceField '{self.name}': Could not find original value for submitted string '{submitted_value_str}' in choices. Returning submitted value as is.")
             cleaned_value = value

        return cleaned_value

class FileField(Field):
    """
    A field that handles file uploads.
    The cleaned value is the uploaded file object itself.
    """
    widget = FileInput

    def __init__(
        self,
        required: bool = True,
        empty_value: Optional[Any] = None,
        allow_empty_file: bool = False,
        max_size: Optional[int] = None,
        allowed_extensions: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """
        Initializes a FileField.

        Args:
            required: If True, a file must be uploaded. Defaults to True.
            empty_value: The cleaned value to return if the field is not required and no file is uploaded.
                         Defaults to None.
            **kwargs: Additional arguments for the base Field class.
        """
        self.empty_value = empty_value
        self.allow_empty_file = allow_empty_file
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions


        super().__init__(required=required, **kwargs) 

        self.error_messages.update({
            'invalid': 'No file was submitted.',
            'required': 'This field is required. Please select a file.',
            'max_size': 'Ensure this file size is not greater than %(limit_value)s bytes (it is %(show_value)s bytes).',
            'allowed_extensions': 'File extension "%(extension)s" is not allowed. Allowed extensions are: %(allowed_extensions)s.',
            'empty_file': 'The submitted file is empty.',
        })


    def to_python(self, value: Any) -> Optional[Any]:
        """
        Validates the uploaded file value.
        The cleaned value is the uploaded file object itself (or None).
        """

        if value is None:
            return self.empty_value if not self.required else None

        if not (hasattr(value, 'read') and callable(value.read) and
                hasattr(value, 'name') and isinstance(value.name, str) and
                hasattr(value, 'size') and isinstance(value.size, int)):
             logger.error(f"FileField: Submitted value does not appear to be a valid file object. Type: {type(value)}, Attributes: {dir(value)}")
             raise ValidationError(self.error_messages['invalid'], code='invalid_file_object')


        if not self.allow_empty_file and value.size == 0:
             raise ValidationError(self.error_messages['empty_file'], code='empty_file')

        if self.max_size is not None and value.size > self.max_size:
             raise ValidationError(
                 self.error_messages['max_size'],
                 code='max_size',
                 params={'limit_value': self.max_size, 'show_value': value.size}
             )

        if self.allowed_extensions:
             _, file_extension = os.path.splitext(value.name)
             if file_extension.lower() not in [ext.lower() for ext in self.allowed_extensions]:
                  raise ValidationError(
                      self.error_messages['allowed_extensions'],
                      code='invalid_extension',
                      params={'extension': file_extension, 'allowed_extensions': ", ".join(self.allowed_extensions)}
                  )
        return value

