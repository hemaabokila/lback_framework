Templating System
=================

The framework uses the Jinja2 templating engine to render dynamic HTML pages.

Within your Views, you can use the ``render`` shortcut function (which leverages the ``TemplateRenderer`` available via Dependency Injection) to render templates:

    .. code-block:: python

        # myapp/views.py
        from lback.utils.shortcuts import render # Assuming 'render' is imported from framework shortcuts
        from .models import Course
        # ...

        def course_list_view(request):
            db_session = request.db_session
            courses = db_session.query(Course).all()
            context = {
                "courses": courses, 
            }
            return render(request, "course_list.html", context) # Render the template

How the ``render`` Shortcut Works
-------------------------------

The ``render`` function simplifies template rendering by automatically handling common tasks.

It retrieves the ``TemplateRenderer`` from the request context and injects crucial data into your

template, such as:

- ``request``: The incoming Request object.
- ``current_user``: Information about the authenticated user.
- ``session``: Session data.
- ``config``: Your application's configuration.
- ``csrf_token``: A token for Cross-Site Request Forgery (CSRF) protection.
- ``static(path)``: A helper function to generate URLs for static files (e.g., CSS, JavaScript, images).

This approach ensures your templates have access to essential application data and security tokens without repetitive manual inclusion in every view.

Example Template (``course_list.html``)
-------------------------------------

Here's how you might structure ``course_list.html`` to display the ``courses`` data passed from

the view:

    .. code-block:: html
        
        <!DOCTYPE html>
        <html>
        <head>
            <title>Course List</title>
        </head>
        <body>
            <h1>All Courses</h1>
            <ul>
                {% for course in courses %}
                    <li>{{ course.title }} - {{ course.created_at.strftime('%Y-%m-%d') }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>

This setup provides a clear and concise way to build dynamic web pages using Jinja2 templates in your Lback Framework application.