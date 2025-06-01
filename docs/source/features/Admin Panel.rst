Built-in Admin Panel
====================

The Lback Framework comes with a powerful and ready-to-use **administrative panel** designed to simplify the management of your application's data models. This panel automatically generates user interfaces for common database operations (Create, Read, Update, Delete), significantly reducing the boilerplate code you need to write for data management.

---

1. Accessing the Admin Panel
----------------------------

The Admin panel URLs are typically included under the ``/admin/`` prefix in your project's main URL configuration file (e.g., ``myproject/urls.py``):

.. code-block:: python

    # myproject/urls.py
    from lback.core.urls_utils import include

    urlpatterns = [
        # ... other paths ...
        include('lback.admin.urls', prefix='/admin/'),
    ]

Once configured, you can access the admin panel by navigating to ``/admin/`` in your web browser. You'll need to log in with an **admin user account** (e.g., a Supreme Admin or Super-admin) to gain access.

---

2. Registering Your Models
--------------------------

To make your application's data models manageable through the Admin panel, you need to **register** them. This is typically done within an ``admin.py`` file inside your application directory.

When you register a model, the framework automatically generates:

* A list view showing all instances of that model.
* An ``Add`` form to create new instances.
* A ``Change`` form to modify existing instances.
* A ``Delete`` action for removing instances.

**Example:** Registering a ``Course`` Model

Assuming you have a ``Course`` model defined (e.g., in ``myapp/models.py``):

.. code-block:: python

    # myapp/admin.py
    from lback.admin.registry import admin
    from .models import Course, Student # Import the models you want to manage

    # Register the Course model
    admin.register(Course)

    # You can register multiple models
    admin.register(Student)

---

3. Admin Panel and ModelForm Integration
----------------------------------------

The Admin panel heavily leverages the framework's ``ModelForm`` system. When you register a model, the Admin panel automatically generates a ``ModelForm`` for it behind the scenes to handle data input, validation, and saving.

For more advanced control over the forms used in the Admin panel (e.g., custom validation, custom widgets, specific field ordering), you can provide a custom ``ModelForm`` when registering your model.

**Example:** Registering with a Custom ``ModelForm``

Let's say you want to customize the ``Course`` form in the admin to use a ``Textarea`` for the description and add custom validation:

First, define your ``ModelForm`` (e.g., in ``myapp/forms.py``):

.. code-block:: python

    # myapp/forms.py
    from lback.forms.models import ModelForm
    from lback.forms.widgets import Textarea
    from lback.forms.validation import ValidationError
    from .models import Course

    class CourseAdminForm(ModelForm):
        class Meta:
            model = Course
            fields = ['name', 'description', 'duration_hours', 'is_active'] # Specify fields
            widgets = {
                'description': Textarea(attrs={'rows': 5, 'cols': 60}),
            }

        def clean_duration_hours(self):
            duration = self.cleaned_data.get('duration_hours')
            if duration and duration <= 0:
                raise ValidationError("Course duration must be a positive number.")
            return duration

Then, register your model with this custom form:

.. code-block:: python

    # myapp/admin.py
    from lback.admin.registry import admin
    from .models import Course
    from .forms import CourseAdminForm # Import your custom ModelForm

    class CourseAdminConfig:
        # Link the custom ModelForm to the admin configuration for Course
        form_class = CourseAdminForm
        # You can also add other configurations like list_display, search_fields here
        list_display = ['name', 'duration_hours', 'is_active']
        search_fields = ['name', 'description']

    # Register the Course model with its custom configuration
    admin.register(Course, CourseAdminConfig)

---

4. Admin Panel and User Permissions
-----------------------------------

The Admin panel is fully integrated with the framework's **Admin User Permissions and Hierarchy** system (as detailed in the :ref:``authorization`` section).

Access to specific models and actions (add, change, view, delete) within the Admin panel is strictly controlled by the permissions assigned to the logged-in admin user.

* **Supreme Admin (User ID 1)** and **Super-admin** (``is_superuser=True``) users automatically have full access to all registered models and actions.
* **Regular Admin** users' access is determined by the specific ``add_<model_name>``, ``change_<model_name>``, ``view_<model_name>``, and ``delete_<model_name>`` permissions assigned to their **Admin User Groups**.

The Admin panel itself is where you manage these **Admin Users**, **Admin User Groups**, and their **permissions**, providing a centralized control point for your application's administrative access.

---

5. Key Features and Customization
---------------------------------

The Built-in Admin Panel offers several features for efficient data management:

* **Auto-generated CRUD Interfaces:** Immediately get functional forms and lists for your models upon registration.
* **User and Permission Management:** The primary interface for creating and managing all types of users (standard and admin), user groups, and their associated permissions.
* **Search and Filtering:** Basic search and filtering capabilities for registered models.
* **Customization Options:** Beyond providing a custom ``form_class``, you can configure ``list_display`` (columns to show in list view), ``search_fields`` (fields to enable search on), and more through the ``AdminConfig`` class when registering models.
* **Extensibility:** While providing a robust default, the admin panel is designed to be extendable if you need highly specialized views or functionality not covered by the generic interface.

For detailed information on configuring specific aspects of the Admin panel and its underlying permission system, refer to the :ref: ``authorization`` documentation.

---

**[Optional: Placeholder for Screenshots]**

*Include screenshots here showing:*
* *The main Admin dashboard.*
* *An example list view for a registered model (e.g., 'Courses').*
* *An example 'Add' or 'Change' form for a model, possibly showing a custom widget.*
* *The User/Group/Permission management interfaces.*