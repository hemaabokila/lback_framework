def file_extension_filter(value):
    """
    Custom Jinja2 filter to extract file extension from a string.
    Returns lowercase extension or empty string if not applicable.
    """
    if not isinstance(value, str):
        return ""
    parts = value.split('.')
    if len(parts) > 1:
        return parts[-1].lower()
    else:
        return ""

def split_filter(value, sep=None):
    """
    Custom Jinja2 filter to split a string into a list.
    Usage in template: {{ value | split('.') }}
    """
    if not isinstance(value, str):
        return []
    return value.split(sep)
import datetime

def date_filter(value, format_string="%Y"):
    """
    Jinja2 filter to format datetime objects.
    By default, it formats to the year (%Y).

    Example usage in Jinja2:
    {{ "now" | date("%Y") }}
    {{ some_datetime_object | date("%Y-%m-%d") }}
    """
    if isinstance(value, datetime.datetime):
        return value.strftime(format_string)
    elif value == "now":
        return datetime.datetime.now().strftime(format_string)
    else:
        return value


CUSTOM_FILTERS = {
    'file_extension': file_extension_filter,
    'split': split_filter,
    'date': date_filter,
}
