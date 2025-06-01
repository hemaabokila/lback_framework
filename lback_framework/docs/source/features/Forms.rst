Forms
=====

The framework provides a powerful and flexible Forms system designed to handle HTML form rendering, data validation, and processing with ease.

It abstracts away common boilerplate, allowing you to focus on your application's logic.

1- Defining Forms
-----------------

Forms are defined as Python classes that inherit from ``lback.forms.forms.Form```.

You declare form fields as class attributes, and the framework's ``FormMetaclass`` automatically collects the

**Example: A Simple Contact Form**

Let's look at how you'd define a contact form:

    .. code-block:: python

        # myapp/forms.py
        from lback.forms.fields import CharField, EmailField, IntegerField, BooleanField
        from lback.forms.widgets import Textarea, CheckboxInput, PasswordInput
        from lback.forms.forms import Form
        from lback.forms.validation import ValidationError # For custom validation

        class ContactForm(Form):
            """
            A simple form for contact inquiries.
            Demonstrates various field types and custom validation.
            """
            name = CharField(
                min_length=3,
                max_length=100,
                required=True,
                label="Your Name",
                help_text="Please enter your full name."
            )
            email = EmailField(
                required=True,
                label="Your Email"
            )
            age = IntegerField(
                min_value=18,
                max_value=99,
                required=False,
                label="Your Age",
                help_text="Must be between 18 and 99."
            )
            message = CharField(
                required=True,
                widget=Textarea(attrs={'rows': 5, 'cols': 40}), # Custom widget with HTML attributes
                label="Your Message"
            )
            newsletter_signup = BooleanField(
                required=False,
                label="Sign up for newsletter?",
                widget=CheckboxInput # Explicitly setting checkbox widget
            )
            password = CharField(
                required=False,
                widget=PasswordInput, # Renders as <input type="password">
                label="Password (optional)"
            )
            password_confirm = CharField(
                required=False,
                widget=PasswordInput,
                label="Confirm Password"
            )

            # You can add custom validation logic that applies to a single field
            def clean_name(self, value):
                """Custom validation for the 'name' field."""
                if "admin" in value.lower():
                    raise ValidationError("Name cannot contain 'admin'.", code='invalid_name')
                return value

            # You can add custom validation logic that applies to the entire form (multiple fields)
            def clean(self):
                """
                Performs form-level validation.
                This method is called after individual field validations are complete.
                """
                # Always call the super().clean() to ensure base validations and initial clean_data.
                # This base clean() method already handles password mismatch, for example.
                super().clean() 

                # Access cleaned data from individual fields
                name = self.cleaned_data.get('name')
                email = self.cleaned_data.get('email')

                # Example of cross-field validation
                if name and email and name.lower() == email.split('@')[0].lower():
                    raise ValidationError("Name cannot be the same as the email's local part.", code='name_email_match')

                return self.cleaned_data

2- Form Lifecycle & Usage
--------------------------

Working with forms typically involves these steps:

**a. Instantiating a Form**

You can instantiate a form in two main ways:
* **Unbound Form (GET requests):** Used when initially displaying an empty form or a form pre-filled with initial data.

    .. code-block:: python

        # To display an empty form
        form = ContactForm()

        # To display a form with initial values (e.g., for editing an existing entry)
        initial_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        form = ContactForm(initial=initial_data)

* **Bound Form (POST requests):** Used when processing submitted data from a user.

The ``data`` and ``files`` arguments should come directly from your request object (e.g., ``request.POST``, ``request.FILES``).

    .. code-block:: python

        # In your view handling a POST request
        form = ContactForm(data=request.POST, files=request.FILES)

**b. Validating Form Data** (``is_valid()``)

After instantiating a bound form, you must call the ``is_valid()`` method to trigger the validation process.

This method validates each field individually and then calls the form's ``clean()`` method for form-level validation.

    .. code-block:: python

        # In your view
        form = ContactForm(data=request.POST)

        if form.is_valid():
            # Form data is valid, access cleaned data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            # ... process data (e.g., save to database)
            return redirect('/success-page/')
        else:
            # Form data is invalid, render the form again with errors
            # The template will use form.errors to display feedback
            return render(request, 'contact.html', {'form': form})

**c. Accessing Cleaned Data** (``cleaned_data``)

If ``is_valid()`` returns ``True``, the validated and converted data for each field is available in the ``form.cleaned_data`` property.

This dictionary contains the final, processed values ready for use (e.g., saving to a database).

    .. code-block:: python

        if form.is_valid():
            user_name = form.cleaned_data['name'] # This will be the cleaned string
            user_age = form.cleaned_data['age']   # This will be an integer, or None if not required
            # ...

**d. Handling Errors** (``errors``, ``non_field_errors``)

If ``is_valid()`` returns ``False``, you can access the validation errors through:

* ``form.errors``: A dictionary where keys are field names and values are lists of ``ValidationError`` objects for that field.It also contains the ``__all__`` key for form-level errors.
* ``form.non_field_errors``: A convenient property that returns a list of errors that are not specific to any single field (i.e., errors from the ``clean()`` method).

You typically pass the form object back to your template to display these errors next to the relevant fields.

3- Field Types
--------------

The framework provides a variety of built-in field types to handle different kinds of data:

* ``CharField``: For single-line text input.
    * **Options:** ``min_length``, ``max_length``.
* ``EmailField``: Specifically for email addresses, includes email format validation.
* ``IntegerField``: For whole numbers.
    * **Options:** ``min_value``, ``max_value``.
* ``BooleanField``: For true/false values, typically rendered as checkboxes.
* ``ChoiceField``: For selecting one option from a predefined set.
    * **Options:** choices (a list of tuples, e.g., ``[('M', 'Male'), ('F', 'Female')]``).
* ``DateField``: For dates.
* ``TimeField``: For times.
* ``DateTimeField``: For date and time.
* ``FileField``: For file uploads.

All fields support common arguments:

* ``required``: ``True`` by default. If ``False``, the field can be left empty.
* ``label``: The human-readable label for the field in the HTML form.
* ``initial``: The initial value to populate the field with when the form is unbound.
* ``help_text``: Explanatory text displayed next to the field.
* ``widget``: Allows you to specify a custom HTML widget for the field.

4. Widgets
----------

Widgets determine how a form field is rendered as HTML.

You can specify a custom widget using the ``widget`` argument when defining a field.
* ``TextInput``: Default for ``CharField``, ``EmailField``, ``IntegerField``.
* ``Textarea``: For multi-line text input.
* ``PasswordInput``: Renders an ``<input type="password">`` field.
* ``CheckboxInput``: Renders an ``<input type="checkbox">`` field.
* ``Select``: Renders a ``<select>`` dropdown for ``ChoiceField``.
* ``DateInput``: Renders an ``<input type="date">` for `DateField``.
* ``TimeInput``: Renders an ``<input type="time">` for `TimeField``.
* ``DateTimeInput``: Renders an ``<input type="datetime-local">`` for ``DateTimeField``.
* ``FileInput``: Renders an ``<input type="file">`` for ``FileField``.
You can also pass ``attrs`` (attributes) to widgets to customize their HTML properties:

    .. code-block:: python

        message = CharField(
            widget=Textarea(attrs={'rows': 5, 'class': 'my-custom-textarea'}),
            label="Your Message"
        )

Then, in your ``contact.html`` template, you can render the form using one of these methods:

* ``{{ form.as_p }}``: Renders each field wrapped in ``<p>`` tags.

    .. code-block:: html

        <form method="post">
            {{ form.as_p }}
            <button type="submit">Submit</button>
        </form>

* ``{{ form.as_ul }}``: Renders each field wrapped in ``<li>`` tags, inside a ``<ul>``.

    .. code-block:: html

        <form method="post">
            <ul>
                {{ form.as_ul }}
            </ul>
            <button type="submit">Submit</button>
        </form>

* ``{{ form.as_table }}``: Renders each field as a row (``<tr>``) in an HTML ``<table>``.

    .. code-block:: html

        <form method="post">
            <table>
                {{ form.as_table }}
            </table>
            <button type="submit">Submit</button>
        </form>

All rendering methods automatically include labels, input fields, error messages, and help text.

Non-field errors are displayed at the top of the form.

6- ``ModelForm``
--------------
Connecting Forms to Database Models

``ModelForm`` is a powerful tool within this framework, designed to simplify the creation of forms that interact directly with your database models (SQLAlchemy models).

Instead of manually defining each field in your form, ``ModelForm`` can automatically generate fields from your model's columns, saving you significant time and effort while reducing repetitive boilerplate code.

**When to Use** ``ModelForm``?

Use `ModelForm` when you have a database model and want to create a form for entering new data for that model, or for editing existing model instances.

It's ideal for common CRUD (Create, Read, Update, Delete) operations related to your database entities.

**How to Define a** ``ModelForm``

To define a ``ModelForm``, you create a class that inherits ``from lback.forms.models.ModelForm`` and define an inner class named ``Meta``.

Inside ``Meta``, you must specify the database model that the form will operate on.

**Example: A Simple Product Form**

Let's use a `Product` model (assuming the content of ``myapp/models/product.py`` is as follows):

    .. code-block:: python
        # myapp/models/product.py
        from sqlalchemy import Column, Integer, String, Float, Boolean, Text
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class Product(Base):
            __tablename__ = 'products'
            id = Column(Integer, primary_key=True)
            name = Column(String(255), nullable=False)
            description = Column(Text, nullable=True)
            price = Column(Float, nullable=False)
            is_available = Column(Boolean, default=True)
            stock_quantity = Column(Integer, default=0)

            def __repr__(self):
                return f"<Product(id={self.id}, name='{self.name}')>"

Now, let's define the `ModelForm` for this model:

    .. code-block:: python

        # myapp/forms.py
        from lback.forms.models import ModelForm
        from lback.forms.fields import CharField # For adding non-model fields or overriding
        from lback.forms.widgets import Textarea, TextInput # For customizing widgets
        from lback.forms.validation import ValidationError # For custom validation
        from lback.models.product import Product # Import your Product model

        class ProductForm(ModelForm):
            class Meta:
                # Specify the database model this form will interact with
                model = Product

                # 'fields': A list of column names from the model to include in the form.
                # Fields for these columns will be automatically generated.
                fields = ['name', 'description', 'price', 'is_available', 'stock_quantity']

                # 'exclude': A list of column names from the model to exclude from the form.
                # If you specify 'fields', 'exclude' is ignored.
                # exclude = ['id', 'created_at']

                # 'widgets': A dictionary allowing you to specify a custom widget for a
                # particular field instead of its default widget.
                widgets = {
                    'description': Textarea(attrs={'rows': 4, 'class': 'form-control-textarea'}),
                    'name': TextInput(attrs={'placeholder': 'Enter product name'}),
                }

                # 'field_classes': (Advanced use) A dictionary allowing you to specify a custom
                # Field class for a particular field instead of the automatically generated one.
                # field_classes = {
                #     'name': CustomCharField # 'CustomCharField' would need to be defined
                # }

            # You can define additional fields here that don't directly correspond to model columns.
            # Note that these fields will NOT be automatically saved by form.save() to the model.
            # agreement = BooleanField(label="I agree to terms and conditions", required=True)

            # You can also override an automatically generated field from the model by defining it here.
            # For example, to increase the min_length for the 'name' field or change its label:
            # name = CharField(min_length=5, max_length=100, label="Product Title")

            # As with the base Form, you can add custom form-level validation logic here.
            def clean(self):
                """
                Performs form-wide validation.
                This method is called after individual field validations are complete.
                """
                # Always call super().clean() to ensure base validations are applied.
                super().clean()

                # Example of cross-field validation:
                # Ensure that the product price is not negative if it's available (hypothetical logic)
                price = self.cleaned_data.get('price')
                is_available = self.cleaned_data.get('is_available')

                if price is not None and price < 0 and is_available:
                    self.add_error('price', ValidationError("Product cannot be available with a negative price.", code='invalid_price_availability'))
                
                return self.cleaned_data

``ModelForm`` **Lifecycle & Usage**

Using a ``ModelForm`` follows the same lifecycle as the base ``Form``, with a key added benefit: the ability to save data directly to your database.

**a. Instantiating a** ``ModelForm``

* **Unbound Form:** Used to display an empty form or a form pre-filled with initial data.

    .. code-block:: python
        
        # To display an empty form for creating a new object
        form = ProductForm()

        # To display a form pre-filled with initial values (just like a regular Form)
        initial_data = {'name': 'Sample Product', 'price': 10.99}
        form = ProductForm(initial=initial_data)

* **Bound Form:** For processing submitted data (typically from a ``POST`` request).

    .. code-block:: python
        # In your view handling a POST request
        # Make sure to pass request.form for data and request.files for file uploads
        form = ProductForm(data=request.form, files=request.files)

* **Bound Form with an Existing Object** (``instance``): For modifying an existing database 

object. This is one of the most powerful features of ``ModelForm``.

When you pass a model instance to the ``instance`` argument, the form will automatically populate its fields with that object's current values. When you then save the form, it will update this existing object instead of creating a new one.

    .. code-block:: python

        from lback.models.product import Product # Import your Product model
        from lback.models.database import db_session # Assuming you have a db_session

        # Retrieve an existing Product object from the database
        existing_product = db_session.query(Product).get(product_id)

        # To populate the form with the product's data and display it for editing
        form = ProductForm(instance=existing_product)

        # To process POST data for updating the product
        form = ProductForm(data=request.form, files=request.files, instance=existing_product)

**b. Validating Form Data (`is_valid()`)**

Just like with `Form`, you must call `is_valid()` to trigger the validation process.

    .. code-block:: python

        # In your view
        # ... (Obtain request.form and request.files data)
        form = ProductForm(data=request.form, files=request.files)

        if form.is_valid():
            # Data is valid; access it via form.cleaned_data
            product_name = form.cleaned_data['name']
            # ...
            # Now you can proceed to save the data
        else:
            # Data is invalid; re-render the form with errors
            # Your template will use form.errors to display feedback
            return render(request, 'product_form.html', {'form': form})

**c. Accessing Cleaned Data** (``cleaned_data``)

Upon a successful ``is_valid()`` call, the validated, converted, and processed data for each field will be available in the ``form.cleaned_data`` property.

This dictionary contains the final values ready for use (e.g., saving to a database).

**d. Saving Data** (``save()``)

This is the core feature of ``ModelForm``.

After successful validation, you can use the ``save()`` method to persist the data to your database.

    .. code-block:: python

        from sqlalchemy.orm import Session as DBSession # Ensure you import your DB session
        from lback.core.response import Response # Assuming your Response object
        import logging # For logging errors
        logger = logging.getLogger(__name__)

        # ... inside your view after form.is_valid() check
        try:
            # If the form was initialized without an 'instance', save() will create a new Product object.
            # If the form was initialized with an 'instance', save() will update that existing object.
            
            # You MUST pass your SQLAlchemy session to the save() method.
            product_instance = form.save(db_session=db_session, commit=True) # commit=True is the default
            print(f"Product '{product_instance.name}' saved successfully!")
            return Response("Product saved successfully!", status=201) # Or redirect

        except SQLAlchemyError as e:
            # Handle database-specific errors
            db_session.rollback() # Rollback any changes in case of a database error
            logger.error(f"Database error saving product: {e}", exc_info=True)
            return Response(f"Error saving product: {e}", status=500)
        except Exception as e:
            # Handle unexpected general errors
            logger.exception(f"Unexpected error saving product: {e}")
            return Response(f"An unexpected error occurred: {e}", status=500)

* **commit argument:**

    * By default, ``save()`` will perform a ``db_session.commit()`` after adding/updating the object.

    * If you set ``commit=False``, the object will be added/updated in the session but the changes will not be committed to the database.
This is useful if you need to perform additional operations on the object or session before the final commitment.
In this case, you will be responsible for calling ``db_session.commit()`` or ``db_session.rollback()`` yourself.

    .. code-block:: python

        # Example: Saving with commit=False for additional processing
        if form.is_valid():
            product = form.save(db_session=db_session, commit=False)
            # Now you can make additional modifications to 'product'
            # or add other objects to the session
            # product.last_edited_by = request.user.id # Assuming you have a user in request
            db_session.add(product) # Re-add if detached or to re-confirm
            db_session.commit()
            return Response("Product saved and processed!", status=200)

**e. Handling File Fields** (``FileField``) **in** ``ModelForm``

If your model includes a SQLAlchemy column of type ``LargeBinary`` (used for storing binary file data), ``ModelForm`` can automatically handle ``FileFields``.

When a file is uploaded, ``save()`` will read the file's content, convert it to bytes, and store it in the LargeBinary column.

    .. code-block:: python

        # myapp/models/document.py (Example of a model storing files)
        from sqlalchemy import Column, Integer, String, LargeBinary
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class Document(Base):
            __tablename__ = 'documents'
            id = Column(Integer, primary_key=True)
            title = Column(String(255), nullable=False)
            content = Column(LargeBinary, nullable=False) # This column stores the binary file data
            original_filename = Column(String(255)) # To store the original file name
            size_bytes = Column(Integer) # To store the file size

        # myapp/forms.py
        from lback.forms.models import ModelForm
        from lback.forms.fields import FileField # Make sure to import FileField
        from lback.forms.validation import ValidationError
        from lback.models.document import Document

        class DocumentForm(ModelForm):
            class Meta:
                model = Document
                fields = ['title', 'content'] # 'content' is your FileField

            def clean_content(self):
                """
                You can add file-specific validations here (e.g., file type, max size).
                """
                uploaded_file = self.cleaned_data.get('content')
                if uploaded_file:
                    # You can access properties of the uploaded file
                    if uploaded_file.size > 5 * 1024 * 1024: # 5MB limit
                        raise ValidationError("File size exceeds 5MB.", code='file_too_large')
                    
                    # You can modify cleaned_data to add other file properties to your model
                    self.cleaned_data['original_filename'] = uploaded_file.name
                    self.cleaned_data['size_bytes'] = uploaded_file.size
                return uploaded_file
