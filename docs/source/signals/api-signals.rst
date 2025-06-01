.. _base-view-signals:

Signals from BaseView
=====================

The :py:class:`lback.views.base_view.BaseView` class, serving as the foundation for all view handlers, emits signals throughout its request dispatching process. These signals offer valuable insights into the lifecycle of a request within a view and enable you to execute custom logic at pivotal moments.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``view_dispatch_started``
     - Emitted at the very beginning of the :py:meth:`~lback.views.base_view.BaseView.dispatch` method, indicating that an incoming request is about to be handled by a specific view instance.
     - ``sender`` (:py:class:`~lback.views.base_view.BaseView`): The instance of the view handling the request.<br>``view_instance`` (:py:class:`~lback.views.base_view.BaseView`): A direct reference to the view instance (same as `sender`).<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``method`` (:py:class:`str`): The HTTP method of the request (e.g., "GET", "POST").<br>``path`` (:py:class:`str`): The URL path of the incoming request.
   * - ``view_method_not_allowed``
     - Emitted when the HTTP request method is not permitted by the :py:attr:`~lback.views.base_view.BaseView.methods` attribute of the view (e.g., a POST request attempting to access a view configured for GET only). This occurs before raising a :py:exc:`~lback.core.exceptions.MethodNotAllowed` exception.
     - ``sender`` (:py:class:`~lback.views.base_view.BaseView`): The view instance.<br>``view_instance`` (:py:class:`~lback.views.base_view.BaseView`): A direct reference to the view instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``method`` (:py:class:`str`): The disallowed HTTP method.<br>``path`` (:py:class:`str`): The URL path of the incoming request.<br>``allowed_methods`` (:py:class:`list` of :py:class:`str`): A list of methods explicitly allowed by the view.
   * - ``view_handler_not_implemented``
     - Emitted when the view technically allows a specific HTTP method but *lacks* a corresponding callable handler method (e.g., a "GET" request is permitted, but no :py:meth:`~lback.views.base_view.BaseView.get()` method is defined in the view). This occurs before raising a :py:exc:`NotImplementedError`.
     - ``sender`` (:py:class:`~lback.views.base_view.BaseView`): The view instance.<br>``view_instance`` (:py:class:`~lback.views.base_view.BaseView`): A direct reference to the view instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``method`` (:py:class:`str`): The HTTP method for which the handler is absent.<br>``path`` (:py:class:`str`): The URL path of the incoming request.<br>``handler_name`` (:py:class:`str`): The expected name of the handler method (e.g., "get", "post").
   * - ``view_dispatch_succeeded``
     - Emitted after a view's method handler (e.g., :py:meth:`~lback.views.base_view.BaseView.get()`, :py:meth:`~lback.views.base_view.BaseView.post()`) has successfully executed and returned a response.
     - ``sender`` (:py:class:`~lback.views.base_view.BaseView`): The view instance.<br>``view_instance`` (:py:class:`~lback.views.base_view.BaseView`): A direct reference to the view instance.<br>``request`` (:py:class:`~lback.core.types.Request`): The incoming request object.<br>``method`` (:py:class:`str`): The HTTP method that was successfully handled.<br>``path`` (:py:class:`str`): The URL path of the incoming request.<br>``response`` (:py:class:`Any`): The response object or data returned by the successful handler.

.. _api-docs-signals:

Signals from APIDocs
====================

The :py:class:`lback.api.docs.APIDocs` class, which handles the generation of OpenAPI (Swagger) documentation, emits signals at various key points throughout its documentation process. These signals offer powerful hooks for **monitoring, extending, or deeply customizing** how your API documentation is generated and integrated.

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``api_docs_initialized``
     - Emitted right after the :py:class:`APIDocs` instance is created and set up with its initial configuration (like title, version, and description).
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The specific instance of the API documentation generator.<br>``title`` (:py:class:`str`): The configured title for the API documentation.<br>``version`` (:py:class:`str`): The configured API version.<br>``description`` (:py:class:`str`): The configured description of the API.
   * - ``api_docs_collection_started``
     - Emitted just as the :py:meth:`~lback.api.docs.APIDocs.collect_documentation` method begins. This signifies the start of gathering documentation details from all registered routes and views.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.
   * - ``api_docs_collection_finished``
     - Emitted once the :py:meth:`~lback.api.docs.APIDocs.collect_documentation` method has finished scanning all routes and views.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.<br>``paths_count`` (:py:class:`int`): The total count of unique API paths that were successfully documented.<br>``processed_routes`` (:py:class:`int`): The number of routes that were processed for documentation, meaning an attempt was made to document them.<br>``skipped_routes`` (:py:class:`int`): The number of routes that were not documented, often due to missing information or uncallable handlers.
   * - ``api_docs_route_documented``
     - Emitted each time a specific route's HTTP methods are successfully inspected and documented for the OpenAPI specification.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.<br>``route`` (:py:class:`~lback.routing.Route`): The route object that was documented.<br>``path`` (:py:class:`str`): The original path string for the route.<br>``documented_methods_count`` (:py:class:`int`): The number of individual HTTP methods (e.g., GET, POST, PUT) found and documented for this particular route.
   * - ``api_docs_route_skipped``
     - Emitted when a route cannot be documented. This is typically due to issues like missing HTTP methods on its associated view class, or if no callable handlers are found for the declared methods.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.<br>``route`` (:py:class:`~lback.routing.Route`): The route object that was skipped.<br>``reason`` (:py:class:`str`): A descriptive string explaining why the route was skipped (e.g., "no_methods", "no_callable_methods").
   * - ``openapi_spec_generated``
     - Emitted after the complete OpenAPI specification dictionary (the final Swagger JSON structure) has been successfully assembled.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.<br>``spec`` (:py:class:`dict`): The entire OpenAPI specification dictionary.
   * - ``api_docs_serializer_schema_registered``
     - Emitted just before a :py:class:`~lback.api.serializer.BaseModelSerializer` class is analyzed to generate its corresponding OpenAPI schema and add it to the global components.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.<br>``serializer_class`` (:py:class:`Type`[:py:class:`~lback.api.serializer.BaseModelSerializer`]): The specific serializer class being processed.<br>``schema_name`` (:py:class:`str`): The name under which this schema will be known within the OpenAPI ``#/components/schemas/`` section.
   * - ``api_docs_serializer_schema_registered_finished``
     - Emitted after a serializer's schema has been fully generated and successfully added to the OpenAPI components section.
     - ``sender`` (:py:class:`~lback.api.docs.APIDocs`): The API documentation generator instance.<br>``schema_name`` (:py:class:`str`): The name of the schema that was just registered.

.. _base-model-serializer-signals:

Signals from BaseModelSerializer
================================

The :py:class:`lback.api.serializer.BaseModelSerializer` class, a foundational component for data serialization and validation within the framework, emits a comprehensive range of signals throughout its operational lifecycle. These signals are incredibly valuable, offering powerful extension points for **auditing data operations, integrating with other parts of your application, or implementing custom logic at critical serialization and validation stages.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``serializer_initialized``
     - Emitted immediately after a serializer instance has been fully initialized and is ready for use.
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The specific serializer instance that was initialized.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the same serializer instance (identical to ``sender``).<br>``many`` (:py:class:`bool`): Indicates if the serializer is configured to handle multiple model instances (e.g., a list of objects).<br>``partial`` (:py:class:`bool`): Indicates if the serializer is configured to allow partial updates (i.e., not all required fields must be present).<br>``context`` (:py:class:`dict`): Any context dictionary passed to the serializer upon initialization.
   * - ``serializer_pre_serialize``
     - Emitted just before the serialization process commences. This is the stage where a model instance (or instances) is about to be transformed into its dictionary representation.
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``instance`` (:py:class:`Any` or :py:class:`list`): The model instance(s) that are currently being prepared for serialization.<br>``many`` (:py:class:`bool`): Indicates if multiple instances are being serialized in this operation.
   * - ``serializer_post_serialize``
     - Emitted immediately after the serialization process has successfully completed, and the dictionary representation of the data is now fully available.
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``serialized_data`` (:py:class:`dict` or :py:class:`list` of :py:class:`dict`): The final data output from the serialization process.
   * - ``serializer_validation_started``
     - Emitted precisely when the validation process begins. This is the stage where raw input data is being processed and checked for correctness, prior to being converted into a clean, validated dictionary. **Sensitive data like passwords will be masked within ``raw_data`` for security.**
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``raw_data`` (:py:class:`dict`): The raw input data dictionary submitted for validation. (Note: sensitive fields like 'password' are masked).
   * - ``serializer_validation_succeeded``
     - Emitted when the entire validation process successfully finishes, providing the cleaned, type-converted, and fully validated data.
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``validated_data`` (:py:class:`dict`): The dictionary containing the validated and cleaned data.
   * - ``serializer_validation_failed``
     - Emitted when the validation process encounters one or more errors. This signal provides details about the validation failures.
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``errors`` (:py:class:`dict`): A dictionary where keys represent field names, and values are lists of associated error messages.<br>``exception`` (:py:class:`Exception`, *optional*): The exception object if the validation failure was caused by an unexpected runtime error.
   * - ``serializer_pre_save``
     - Emitted just before a new model instance is created or an existing one is updated in the database, using the data that has already been validated by the serializer. **Sensitive data like passwords will be masked within ``validated_data`` for security.**
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``validated_data`` (:py:class:`dict`): The validated data dictionary (with sensitive fields masked) that is about to be used for the database save operation.<br>``instance`` (:py:class:`Any` or :py:class:`None`): The existing model instance being updated, or ``None`` if a brand new instance is being created.<br>``session`` (:py:class:`Any`): The database session object that will be utilized for the save operation.
   * - ``serializer_post_save``
     - Emitted immediately after a model instance has been successfully either created or updated in the database.
     - ``sender`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): The serializer instance.<br>``serializer`` (:py:class:`~lback.api.serializer.BaseModelSerializer`): A direct reference to the serializer instance.<br>``instance`` (:py:class:`Any`): The newly created or updated model instance that was persisted to the database.<br>``session`` (:py:class:`Any`): The database session object that was used for the save operation.