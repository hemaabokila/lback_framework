Views & Responses
=================

Views are functions or classes that receive a ``Request`` object and return a ``Response`` object.

They are responsible for the logic of processing the request, interacting with Models and Templates, and generating the appropriate response.

    .. code-block:: python

        # course/views.py
        from lback.utils.shortcuts import render
        from .models import Course
        
        def course_list_view(request):
            db_session = request.db_session
            courses = db_session.query(Course).all()
            context = {
                "courses": courses, 
            }
            return render(request, "course_list.html", context)
        
The framework provides ready-to-use Response classes like ``HTMLResponse``, ``JSONResponse``, ``RedirectResponse``, etc., to simplify response generation.