API Tools
=========

The framework provides a robust set of tools to assist you in building powerful and structured Application Programming Interfaces (APIs):

Serialization:
--------------

The framework offers a dedicated Serializer component (found in ``lback.api.serializer``).

This allows you to efficiently convert complex Python objects (like database models) into standard data formats such as JSON for API responses, and to parse incoming data from requests back into Python objects for validation and saving.

You can define various field types and create custom serializers.

**Example:** Defining a Model Serializer

Here's how you define a serializer for your ``Course`` model, allowing it to be easily converted to
and from JSON:

    .. code-block:: python

        # myapp/serializers.py
        from lback.api.serializer import BaseModelSerializer
        from .models import Course # Assuming your Course model is defined here

        class CourseSerializer(BaseModelSerializer):
            class Meta:
                model = Course
                fields = '__all__' # This includes all fields from the Course model automatically

API Views & Generic Views:
--------------------------

Beyond standard web views, the framework provides specialized **API Views** (from ``lback.api.view``) and **Generic Views** (from ``lback.api.generics``).

These views are designed to handle data-format requests and responses (typically JSON), offering a structured way to define your API endpoints.

The Generic Views provide pre-built functionality for common API operations (CRUD - Create, Read, Update, Delete), allowing you to write less code for standard endpoints.

**Example: Listing and Creating Courses API**

This example demonstrates how to create an API endpoint that lists all courses (``GET`` request) using the ``CourseSerializer`` to format the output:

    .. code-block:: python
        
        # myapp/api_views.py
        from lback.utils.response_helpers import json_response
        from .models import Course
        from .serializers import CourseSerializer # Import your serializer
        
        def api_course_list_create_view(request):
            db_session = request.db_session
        
            if request.method == "GET":
                courses = db_session.query(Course).all()
                serializer = CourseSerializer(instance=courses, many=True)
                return json_response(serializer.data, status=200)
        
API Documentation:
------------------

The framework includes tools for **API Documentation** (``lback.api.docs.APIDocs``).

This feature helps you automatically generate interactive and comprehensive documentation for your API endpoints, making it easier for consumers to understand and integrate with your API.
