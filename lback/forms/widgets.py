from typing import Any, Dict, Optional, List, Tuple

class Widget:
    """
    Base class for all form widgets.
    Widgets are responsible for rendering the HTML representation of a field.
    """
    input_type = None
    template_name = None

    def __init__(self, attrs: Optional[Dict[str, Any]] = None):
        """
        Initializes the widget with optional HTML attributes.

        Args:
            attrs: A dictionary of HTML attributes (e.g., {'class': 'my-input', 'placeholder': 'Enter text'}).
        """
        self.attrs = attrs if attrs is not None else {}

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the widget as an HTML string.
        This method should be overridden by subclasses.

        Args:
            name: The HTML 'name' attribute for the input element.
            value: The current value of the field.
            attrs: Additional HTML attributes to include (merged with self.attrs).

        Returns:
            An HTML string representing the widget.
        """
        raise NotImplementedError("Subclasses must implement the 'render' method.")

    def build_attrs(self, base_attrs: Optional[Dict[str, Any]] = None, extra_attrs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Helper method to combine base attributes, widget attributes, and extra attributes.

        Args:
            base_attrs: Attributes from the field itself.
            extra_attrs: Attributes passed during rendering (e.g., in template tags).

        Returns:
            A combined dictionary of attributes.
        """
        attrs = {}
        if base_attrs:
            attrs.update(base_attrs)
        attrs.update(self.attrs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

    def value_from_datadict(self, data: Dict[str, Any], files: Dict[str, Any], name: str) -> Any:
        """
        Given a dictionary of data and an attribute name, returns the value
        of that attribute, normalizing it if necessary.

        Args:
            data: The dictionary of data (e.g., request.POST).
            files: The dictionary of files (e.g., request.FILES).
            name: The name of the field.

        Returns:
            The raw value from the data dictionary.
        """
        return data.get(name)


class TextInput(Widget):
    """
    A widget that renders as a standard HTML <input type="text">.
    """
    input_type = 'text'

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the text input widget.
        """
        if value is None:
            value = ''

        value_str = str(value)

        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name, 'value': value_str})

        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])

        return f'<input {attrs_string}>'


class Textarea(Widget):
    """
    A widget that renders as an HTML <textarea> element.
    """
    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the textarea widget.
        """
        if value is None:
            value = ''

        value_str = str(value)
        final_attrs = self.build_attrs(attrs, {'name': name})
        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])

        return f'<textarea {attrs_string}>{value_str}</textarea>'

    def value_from_datadict(self, data: Dict[str, Any], files: Dict[str, Any], name: str) -> Any:
        """
        Textarea value is also just retrieved from data dictionary.
        """
        return data.get(name)


class CheckboxInput(Widget):
    """
    A widget that renders as an HTML <input type="checkbox">.
    Handles boolean values.
    """
    input_type = 'checkbox'

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the checkbox input widget.
        Handles setting the 'checked' attribute based on the value.
        """
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})

        if value:
            final_attrs['checked'] = '' 


        if 'value' not in final_attrs:
             final_attrs['value'] = 'on'

        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])

        return f'<input {attrs_string}>'

    def value_from_datadict(self, data: Dict[str, Any], files: Dict[str, Any], name: str) -> Any:
        """
        For checkboxes, the value is only present in data if checked.
        We need to return a boolean based on whether the name exists in data.
        """
        return name in data


class Select(Widget):
    """
    A widget that renders as an HTML <select> element.
    Takes a list of choices.
    """
    def __init__(self, choices: List[Tuple[Any, str]], attrs: Optional[Dict[str, Any]] = None):
        """
        Initializes the Select widget.

        Args:
            choices: A list of (value, label) tuples for the select options.
            attrs: Optional HTML attributes for the <select> element.
        """
        super().__init__(attrs=attrs)
        self.choices = choices

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the select widget with options.
        Handles selecting the correct option based on the current value.
        """
        final_attrs = self.build_attrs(attrs, {'name': name})
        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])

        options_html = []
        for option_value, option_label in self.choices:
            selected_attr = ' selected' if str(value) == str(option_value) else ''
            options_html.append(f'<option value="{option_value}"{selected_attr}>{option_label}</option>')
        return f'<select {attrs_string}>\n{"".join(options_html)}\n</select>'

    def value_from_datadict(self, data: Dict[str, Any], files: Dict[str, Any], name: str) -> Any:
        """
        Select value is retrieved from data dictionary.
        """
        return data.get(name)
    
class PasswordInput(TextInput):
    """
    A widget that displays a password input (<input type="password">).
    By default, it does not pre-fill the value for security reasons.
    """
    input_type = 'password'

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the password input. For security, the value attribute is usually left empty.
        """
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})
        if 'value' in final_attrs:
            del final_attrs['value']

        attr_string = ' '.join(f'{k}="{v}"' for k, v in final_attrs.items() if v is not None)
        return f'<input {attr_string}>'
    
class FileInput(Widget):
    """
    A widget that renders as an HTML <input type="file"> element.
    Handles file uploads.
    """
    input_type = 'file'

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders the file input widget.
        Note: The 'value' attribute is typically NOT set for security reasons
              in file input fields. The browser handles displaying the selected file name.
        """
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})
        attrs_string = " ".join([f'{key}="{value}"' for key, value in final_attrs.items()])

        return f'<input {attrs_string}>'

    def value_from_datadict(self, data: Dict[str, Any], files: Dict[str, Any], name: str) -> Any:
        """
        For file inputs, the value comes from the 'files' dictionary, not 'data'.
        """
        return files.get(name)
