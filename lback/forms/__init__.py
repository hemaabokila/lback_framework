"""
This file serves as the initialization point for the 'lback_framework/lback/forms' package.
It is designed to expose the core components necessary for building, validating, and rendering
web forms within the Lback web framework. This package centralizes the definition and management
of form fields, form classes, validation mechanisms, and various input widgets, providing a
comprehensive system for handling user input.

---

**Key Components Exposed by this Package:**

1.  **Date and Time Fields (from .fields_datetime):**
    A collection of specialized form fields designed to handle date and time input.

    * **DateTimeField:** A form field for capturing both date and time values. It handles
        parsing and formatting of datetime strings.
    * **TimeField:** A form field specifically for capturing time values.
    * **DateField:** A form field specifically for capturing date values.

2.  **File Fields (from .fields_file):**
    A form field dedicated to handling file uploads.

    * **FileField:** A form field for allowing users to upload files. It manages file
        data and provides mechanisms for validation and storage.

3.  **Basic Form Fields (from .fields):**
    A set of fundamental form fields for common data types.

    * **BooleanField:** A form field for capturing boolean (True/False) input, typically
        rendered as a checkbox.
    * **CharField:** A form field for capturing single-line text input, suitable for
        names, titles, or short descriptions.
    * **ChoiceField:** A form field that allows users to select one option from a predefined
        set of choices, often rendered as a dropdown (<select>) or radio buttons.
    * **EmailField:** A specialized form field for capturing email addresses, typically
        including built-in validation for email format.
    * **IntegerField:** A form field for capturing integer (whole number) input.

4.  **Form Classes (from .forms):**
    The core classes for defining and managing forms.

    * **Form:** The base class for creating web forms. It orchestrates the collection of
        fields, handles data binding, and manages the overall validation process for user input.
    * **FormMetaclass:** The metaclass used by the Form class, responsible for processing
        field definitions when a form class is created.

5.  **ModelForm (from .models):**
    A specialized form class designed to work directly with Lback's database models.

    * **ModelForm:** A form class that automatically generates form fields based on a
        given database model's fields. It simplifies the process of creating forms for
        creating or updating model instances, often handling validation and saving to the database.

6.  **Validation (from .validation):**
    Components for handling form and field validation errors.

    * **ValidationError:** A custom exception or class used to signal that form or field
        validation has failed. It typically carries messages detailing the specific validation issues.

7.  **Date and Time Widgets (from .widgets_datetime):**
    HTML input widgets specifically designed for date and time fields.

    * **DateInput:** A widget for rendering a date input field in HTML, often using
        type="date" for native browser date pickers.
    * **DateTimeInput:** A widget for rendering a datetime input field in HTML, often
        using type="datetime-local" or similar.
    * **TextInput:** A generic text input widget, which might be used as a fallback
        or for custom date/time string input.

8.  **File Widgets (from .widgets_file):**
    An HTML input widget for file uploads.

    * **FileInput:** A widget for rendering a file upload input field in HTML (<input type="file">).

9.  **Basic Widgets (from .widgets):**
    Common HTML input widgets for various form fields.

    * **TextInput:** A widget for rendering a standard single-line text input field (<input type="text">).
    * **Textarea:** A widget for rendering a multi-line text input area (<textarea>).
    * **PasswordInput:** A widget for rendering a password input field (<input type="password">),
        masking the input for security.
    * **CheckboxInput:** A widget for rendering a checkbox input field (<input type="checkbox">).
    * **Select:** A widget for rendering a dropdown list (<select>) for choice fields.
"""
