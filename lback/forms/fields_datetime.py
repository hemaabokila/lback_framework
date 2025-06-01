import logging
from typing import Any, Optional, List
from datetime import date, datetime, time

from .widgets_datetime import DateInput, TimeInput, DateTimeInput
from .validation import ValidationError
from .fields import Field

logger = logging.getLogger(__name__)

class DateField(Field):
    """
    A field that handles date input.
    Validates that the input can be converted to a Python date object.
    """
    widget = DateInput

    def __init__(
        self,
        input_formats: Optional[List[str]] = None,
        empty_value: Optional[date] = None,
        **kwargs: Any
    ):
        """
        Initializes a DateField.

        Args:
            input_formats: A list of date format strings to try when parsing the input.
                           Defaults to common formats (e.g., '%Y-%m-%d').
            empty_value: The cleaned value to return if the input is empty and not required.
                         Defaults to None.
            **kwargs: Additional arguments for the base Field class.
        """
        self.input_formats = input_formats if input_formats is not None else [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y',
        ]
        self.empty_value = empty_value
        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid': 'Enter a valid date.',
            'invalid_format': 'Enter a valid date in one of the formats: %(formats)s.',
        })

    def to_python(self, value: Any) -> Optional[date]:
        """
        Converts the input value to a Python date object and performs validation.
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return self.empty_value if not self.required else None

        if isinstance(value, (date, datetime)):
            return value.date() if isinstance(value, datetime) else value

        if not isinstance(value, str):
             raise ValidationError(self.error_messages['invalid'], code='invalid')

        for fmt in self.input_formats:
            try:
                cleaned_value = datetime.strptime(value.strip(), fmt).date()
                logger.debug(f"DateField: Successfully parsed date '{value}' using format '{fmt}'.")
                return cleaned_value

            except (ValueError, TypeError):
                continue

        format_list_str = ", ".join([f"'{fmt}'" for fmt in self.input_formats])
        raise ValidationError(
            self.error_messages['invalid_format'],
            code='invalid_date_format',
            params={'formats': format_list_str}
        )


class TimeField(Field):
    """
    A field that handles time input.
    Validates that the input can be converted to a Python time object.
    """
    widget = TimeInput

    def __init__(
        self,
        input_formats: Optional[List[str]] = None,
        empty_value: Optional[time] = None,
        **kwargs: Any
    ):
        """
        Initializes a TimeField.

        Args:
            input_formats: A list of time format strings to try when parsing the input.
                           Defaults to common formats (e.g., '%H:%M', '%H:%M:%S').
            empty_value: The cleaned value to return if the input is empty and not required.
                         Defaults to None.
            **kwargs: Additional arguments for the base Field class.
        """
        self.input_formats = input_formats if input_formats is not None else [
            '%H:%M:%S',
            '%H:%M',
            '%I:%M:%S %p',
            '%I:%M %p',
        ]
        self.empty_value = empty_value
        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid': 'Enter a valid time.',
            'invalid_format': 'Enter a valid time in one of the formats: %(formats)s.',
        })

    def to_python(self, value: Any) -> Optional[time]:
        """
        Converts the input value to a Python time object and performs validation.
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return self.empty_value if not self.required else None
        
        if isinstance(value, (time, datetime)):
            return value.time() if isinstance(value, datetime) else value
        
        if not isinstance(value, str):
             raise ValidationError(self.error_messages['invalid'], code='invalid')

        for fmt in self.input_formats:
            try:
                cleaned_value = datetime.strptime(value.strip(), fmt).time()
                logger.debug(f"TimeField: Successfully parsed time '{value}' using format '{fmt}'.")
                return cleaned_value

            except (ValueError, TypeError):
                continue

        format_list_str = ", ".join([f"'{fmt}'" for fmt in self.input_formats])
        raise ValidationError(
            self.error_messages['invalid_format'],
            code='invalid_time_format',
            params={'formats': format_list_str}
        )


class DateTimeField(Field):
    """
    A field that handles datetime input.
    Validates that the input can be converted to a Python datetime object.
    """
    widget = DateTimeInput

    def __init__(
        self,
        input_formats: Optional[List[str]] = None,
        empty_value: Optional[datetime] = None,
        **kwargs: Any
    ):
        """
        Initializes a DateTimeField.

        Args:
            input_formats: A list of datetime format strings to try when parsing the input.
                           Defaults to common formats (e.g., '%Y-%m-%dT%H:%M').
            empty_value: The cleaned value to return if the input is empty and not required.
                         Defaults to None.
            **kwargs: Additional arguments for the base Field class.
        """
        self.input_formats = input_formats if input_formats is not None else [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
        ]
        self.empty_value = empty_value
        super().__init__(**kwargs)

        self.error_messages.update({
            'invalid': 'Enter a valid date and time.',
            'invalid_format': 'Enter a valid date and time in one of the formats: %(formats)s.',
        })

    def to_python(self, value: Any) -> Optional[datetime]:
        """
        Converts the input value to a Python datetime object and performs validation.
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return self.empty_value if not self.required else None

        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
             raise ValidationError(self.error_messages['invalid'], code='invalid')
        
        for fmt in self.input_formats:
            try:
                cleaned_value = datetime.strptime(value.strip(), fmt)
                logger.debug(f"DateTimeField: Successfully parsed datetime '{value}' using format '{fmt}'.")
                return cleaned_value

            except (ValueError, TypeError):
                continue

        format_list_str = ", ".join([f"'{fmt}'" for fmt in self.input_formats])
        raise ValidationError(
            self.error_messages['invalid_format'],
            code='invalid_datetime_format',
            params={'formats': format_list_str}
        )
