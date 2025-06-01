import logging
from typing import Any, Dict, Optional
from datetime import date, datetime, time

from .widgets import TextInput

logger = logging.getLogger(__name__)

class DateInput(TextInput):
    """
    A widget that renders as an HTML <input type="date"> or <input type="text">
    for date input.
    """
    input_type = 'date'

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the date input widget.
        Formats the value to 'YYYY-MM-DD' for the HTML date input type.
        """
        if value is None:
            value = ''
        if isinstance(value, (date, datetime)):
            value_to_format = value.date() if isinstance(value, datetime) else value
            value_str = value_to_format.isoformat() 
        else:
            value_str = str(value)
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name, 'value': value_str})
        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])
        return f'<input {attrs_string}>'


class TimeInput(TextInput):
    """
    A widget that renders as an HTML <input type="time"> or <input type="text">
    for time input.
    """
    input_type = 'time'
    
    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the time input widget.
        Formats the value to 'HH:MM' or 'HH:MM:SS' for the HTML time input type.
        """
        if value is None:
            value = ''
        if isinstance(value, (time, datetime)):
            value_to_format = value.time() if isinstance(value, datetime) else value
            if value_to_format.second == 0 and value_to_format.microsecond == 0:
                 value_str = value_to_format.strftime('%H:%M')
            else:
                 value_str = value_to_format.strftime('%H:%M:%S')
        else:
            value_str = str(value)
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name, 'value': value_str})
        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])
        return f'<input {attrs_string}>'


class DateTimeInput(TextInput):
    """
    A widget that renders as an HTML <input type="datetime-local"> or <input type="text">
    for datetime input.
    """
    input_type = 'datetime-local'
    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the datetime input widget.
        Formats the value to 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DDTHH:MM:SS' for HTML.
        """
        if value is None:
            value = ''
        if isinstance(value, datetime):
            value_str = value.isoformat(sep='T', timespec='seconds')
            if value.microsecond == 0:
                 value_str = value.isoformat(sep='T', timespec='minutes')
        else:
            value_str = str(value)
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name, 'value': value_str})
        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])
        return f'<input {attrs_string}>'

