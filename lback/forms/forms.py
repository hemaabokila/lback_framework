import logging
import copy
from typing import Dict, Any, Optional, List


from .fields import Field
from .validation import ValidationError

logger = logging.getLogger(__name__)

class FormMetaclass(type):
    """
    Metaclass for Form classes.
    Automatically collects Field instances defined as class attributes
    into a _declared_fields dictionary.
    """
    def __new__(cls, name, bases, attrs):
        declared_fields = {}

        for key, value in attrs.items():
            if isinstance(value, Field):
                declared_fields[key] = value
                if value.name is None:
                     value.name = key

        attrs['_declared_fields'] = declared_fields

        for field_name in declared_fields.keys():
             attrs.pop(field_name)

        new_class = super().__new__(cls, name, bases, attrs)

        fields_from_bases = {}
        for base in reversed(new_class.__mro__):
             if hasattr(base, '_declared_fields'):
                 fields_from_bases.update(base._declared_fields)

        new_class._declared_fields = fields_from_bases
        new_class._declared_fields.update(declared_fields)

        logger.debug(f"FormMetaclass: Created form class '{name}' with declared fields: {list(new_class._declared_fields.keys())}")

        return new_class


class Form(metaclass=FormMetaclass):
    """
    Base class for all forms.
    Forms are collections of fields that handle data binding and validation.
    Uses FormMetaclass to automatically collect fields defined as class attributes.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None, initial: Optional[Dict[str, Any]] = None):
        """
        Initializes a form instance.

        Args:
            data: A dictionary of data to bind to the form (e.g., from request.POST).
            files: A dictionary of files to bind to the form (e.g., from request.FILES).
            initial: A dictionary of initial data to populate the form with.
        """
        self.data = data
        self.files = files
        self.initial = initial if initial is not None else {}
        self.is_bound = data is not None or files is not None
        self.fields: Dict[str, Field] = {}

        for name, field_instance in self._declared_fields.items():
            field_instance_copy = copy.deepcopy(field_instance)
            field_instance_copy.name = name
            self.fields[name] = field_instance_copy

        self._errors: Optional[Dict[str, List[ValidationError]]] = None
        self._non_field_errors: List[ValidationError] = []
        self._cleaned_data: Dict[str, Any] = {}


        if self.is_bound:
             self._bind_fields()

    def add_error(self, field: Optional[str], error: ValidationError):
        """
        Adds an error to a specific field or to the form's non-field errors.

        Args:
            field: The name of the field to associate the error with. 
                   If None, the error is added to the form's non-field errors.
            error: The ValidationError object containing the error message and code.
        """
        if field is None:
            self._non_field_errors.append(error)
            logger.debug(f"Form: Added non-field error: {error.message}")
        else:
            if field in self.fields:
                self.fields[field].errors.append(error)
                logger.debug(f"Form: Added error to field '{field}': {error.message}")
            else:
                logger.warning(f"Form: Attempted to add error to non-existent field '{field}'. Error: {error.message}")

    def _bind_fields(self):
        """Binds data and files from the request to each field."""
        logger.debug(f"Form: Binding data to fields. Is bound: {self.is_bound}")
        if not self.is_bound:
            logger.warning("Form: _bind_fields called on an unbound form.")
            return

        for name, field in self.fields.items():
            field.bind(name, self.data if self.data is not None else {}, self.files if self.files is not None else {})
            logger.debug(f"Form: Bound field '{name}'.")



    def is_valid(self) -> bool:
        self._errors = {}
        self._non_field_errors = []
        self._cleaned_data = {}

        all_fields_valid = True
        for name, field_instance in self.fields.items():
            if not field_instance.is_valid():
                all_fields_valid = False
                self._errors[name] = field_instance.errors
            else:
                self._cleaned_data[name] = field_instance.cleaned_value

        try:
            self.clean() 
        except ValidationError as e:
            self.add_error(None, e)
            all_fields_valid = False
        except Exception as e:
            logger.exception(f"Form '{self.__class__.__name__}': Unexpected error in clean method: {e}")
            self.add_error(None, ValidationError(f"An internal error occurred: {e}", code='internal_error'))
            all_fields_valid = False
        
        if self._non_field_errors:
            self._errors['__all__'] = self._non_field_errors

        return not bool(self._errors)

    @property
    def errors(self) -> Dict[str, List[ValidationError]]:
        """
        Returns a dictionary of errors for the form.
        Keys are field names, values are lists of ValidationError instances.
        Includes '__all__' key for non-field errors.
        Calls is_valid() implicitly if not already called.
        """
        if self._errors is None:
            self.is_valid()
        return self._errors if self._errors is not None else {}

    @property
    def non_field_errors(self) -> List[ValidationError]:
        """Returns a list of non-field errors."""
        if self._errors is None:
             self.is_valid()
        return self.errors.get('__all__', [])


    @property
    def cleaned_data(self) -> Dict[str, Any]:
        """
        Returns a dictionary of validated and cleaned data for each field.
        Only available if the form is valid.
        """
        if self._errors is None:
            self.is_valid()
        return self._cleaned_data


    def _render_field(self, name: str, field: Field) -> str:
        """Helper to render a single field including label, errors, and help text."""
        output = []

        widget_attrs = field.widget.build_attrs()
        input_id = widget_attrs.get("id", f"id_{name}")

        label_html = f'<label for="{input_id}">{field.label or name}:</label>'
        output.append(label_html)

        field_html = field.render()

        output.append(field_html)

        if field.errors:
            errors_html = '<ul class="errorlist">'
            for error in field.errors:
                errors_html += f'<li>{error}</li>'
            errors_html += '</ul>'
            output.append(errors_html)

        if field.help_text:
            help_text_html = f'<p class="helptext">{field.help_text}</p>'
            output.append(help_text_html)

        return "".join(output)


    def as_p(self) -> str:
        """Renders the form as HTML <p> tags."""
        output = []
        if self.non_field_errors:
             output.append('<ul class="errorlist">')
             for error in self.non_field_errors:
                  output.append(f'<li>{error}</li>')
             output.append('</ul>')

        for name, field in self.fields.items():
            field_content_html = self._render_field(name, field)
            output.append(f'<p>{field_content_html}</p>')

        return "\n".join(output)

    def as_ul(self) -> str:
        """Renders the form as HTML <ul> tags."""
        output = []
        if self.non_field_errors:
            output.append('<ul class="errorlist">')
            for error in self.non_field_errors:
                output.append(f'<li>{error}</li>')
            output.append('</ul>')

        output.append('<ul>')
        for name, field in self.fields.items():
            field_content_html = self._render_field(name, field)
            output.append(f'<li>{field_content_html}</li>')
        output.append('</ul>')

        return "\n".join(output)


    def as_table(self) -> str:
        """Renders the form as an HTML <table>."""
        output = []
        output.append('<table>')
        if self.non_field_errors:
            output.append('<tr><td colspan="2"><ul class="errorlist">')
            for error in self.non_field_errors:
                output.append(f'<li>{error}</li>')
            output.append('</ul></td></tr>')

        for name, field in self.fields.items():
            widget_attrs = field.widget.build_attrs()
            input_id = widget_attrs.get("id", f"id_{name}")

            label_html = f'<label for="{input_id}">{field.label or name}:</label>'
            label_cell = f'<th>{label_html}</th>'

            field_html = field.render()

            errors_html = ''
            if field.errors:
                errors_html = '<ul class="errorlist">'
                for error in field.errors:
                    errors_html += f'<li>{error}</li>'
                errors_html += '</ul>'

            help_text_html = ''
            if field.help_text:
                help_text_html = f'<p class="helptext">{field.help_text}</p>'

            field_cell_content = f'{field_html} {errors_html} {help_text_html}'
            field_cell = f'<td>{field_cell_content}</td>'

            output.append('<tr>')
            output.append(label_cell)
            output.append(field_cell)
            output.append('</tr>')

        output.append('</table>')

        return "\n".join(output)


    def clean(self):
        """
        Performs form-level validation that depends on multiple fields.
        Should raise ValidationError for non-field errors.
        Can also modify self.cleaned_data.
        Subclasses should override this method if form-level validation is needed.
        """
        pass

