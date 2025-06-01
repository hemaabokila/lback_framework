.. _template-renderer-signals:

Signals from TemplateRenderer
=============================

The :py:class:`lback.core.templating.TemplateRenderer` class is responsible for loading and rendering templates, whether they are from the file system or a database. It integrates with the SignalDispatcher to emit signals throughout the template rendering process, providing **detailed insights into template operations, enabling logging, performance monitoring, and custom error handling related to templates.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``template_rendering_started``
     - Emitted at the beginning of a template rendering attempt, whether from the file system or a database.
     - ``sender`` (:py:class:`~lback.core.templating.TemplateRenderer`): The instance of the template renderer.<br>``template_name`` (:py:class:`str`): The name of the template being rendered.<br>``context`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The context dictionary passed to the template.<br>``source`` (:py:class:`str`): Indicates the source of the template (e.g., "filesystem_string", "database", "database_string").
   * - ``template_rendered``
     - Emitted after a template has been successfully rendered to a string (from file system or database).
     - ``sender`` (:py:class:`~lback.core.templating.TemplateRenderer`): The instance of the template renderer.<br>``template_name`` (:py:class:`str`): The name of the template that was rendered.<br>``context`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The full context dictionary used for rendering.<br>``rendered_content`` (:py:class:`str`): The full content of the rendered template.<br>``source`` (:py:class:`str`): Indicates the source of the template (e.class:`str`): The HTTP method of the request.<br>``path`` (:py:class:`str`): The URL path of the request.<br>``full_path`` (:py:class:`str`): The full path including query string.<br>``duration`` (:py:class:`float`): The total time taken to process the request in seconds.<br>``status_code`` (:py:class:`int` or :py:class:`str`): The HTTP status code of the final response (or 'N/A' if unavailable).<br>``response`` (:py:class:`~lback.core.response.Response`, *optional*): The final response object generated.<br>``request`` (:py:class:`~lback.core.types.Request`, *optional*): The request object that was processed.
   * - ``template_rendering_failed``
     - Emitted when a template rendering attempt fails due to a `TemplateNotFound` error or any other exception.
     - ``sender`` (:py:class:`~lback.core.templating.TemplateRenderer`): The instance of the template renderer.<br>``template_name`` (:py:class:`str`): The name of the template that failed to render.<br>``context`` (:py:class:`Dict`[:py:class:`str`, :py:class:`Any`]): The context dictionary passed to the template.<br>``source`` (:py:class:`str`): Indicates the source of the template (e.g., "filesystem_string", "database", "database_string").<br>``error_type`` (:py:class:`str`): Describes the type of failure (e.g., "not_found", "exception", "not_found_in_db").<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an exception.
   * - ``db_template_loading_started``
     - Emitted when the template renderer begins an attempt to load template content from the database.
     - ``sender`` (:py:class:`~lback.core.templating.TemplateRenderer`): The instance of the template renderer.<br>``template_name`` (:py:class:`str`): The name of the template being loaded from the database.
   * - ``db_template_loaded``
     - Emitted after template content has been successfully loaded from the database.
     - ``sender`` (:py:class:`~lback.core.templating.TemplateRenderer`): The instance of the template renderer.<br>``template_name`` (:py:class:`str`): The name of the template that was loaded from the database.<br>``content`` (:py:class:`str`): The raw content of the template loaded from the database.
   * - ``db_template_load_failed``
     - Emitted when an attempt to load template content from the database fails.
     - ``sender`` (:py:class:`~lback.core.templating.TemplateRenderer`): The instance of the template renderer.<br>``template_name`` (:py:class:`str`): The name of the template that failed to load from the database.<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the failure was due to an exception during loading.