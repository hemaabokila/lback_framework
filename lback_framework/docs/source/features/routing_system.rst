Routing System
==============

URL configuration in Lback is usually done in ``urls.py`` files using a ``urlpatterns`` list.

You define patterns that map a URL path to a View function or class to handle the request.

    .. code-block:: python

        # courses/urls.py
        from lback.utils.urls import path
        from .views import course_list_view

        urlpatterns = [
            path("/courses/", course_list_view, allowed_methods=["GET"], name="course_list")
        ]

URL Including
-------------

You can organize app-specific URLs in separate ``urls.py`` files and include them in the main URL configuration using the ``include`` function:

    .. code-block:: python

        # myproject/urls.py
        from lback.core.urls_utils import include

        urlpatterns = [
            include('courses.urls', prefix='/'), # Include course URLs at the root path
            include('lback.admin.urls', prefix='/admin/'), # Include Admin URLs under the /admin/ prefix
            # ... other paths
        ]
