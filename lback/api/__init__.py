"""
This file serves as the initialization point for the 'lback_framework/lback/api' package.
It is designed to expose the core components necessary for building robust RESTful APIs
within the Lback web framework. This package centralizes the definition and management
of API functionalities, including views, serializers, mixins, and documentation tools.

---

**Key Components Exposed by this Package:**

1.  **APIDocs:**
    Manages and generates comprehensive API documentation for the Lback framework. This component
    is crucial for creating structured and interactive documentation (e.g., OpenAPI/Swagger specifications)
    that details all available API endpoints, their expected request formats, and their response structures.
    It aids developers in understanding and integrating with Lback-powered APIs by providing metadata
    like API title, version, and description, and can register endpoints for automatic documentation generation.

2.  **Generic API Views (from .generics):**
    A suite of pre-built, reusable classes designed to handle common RESTful operations (CRUD - Create, Read, Update, Delete)
    with minimal boilerplate code. These views abstract away repetitive logic, allowing for rapid API development.

    * **GenericAPIView:** The foundational class for all generic API views, providing core mechanisms for
        handling HTTP requests, interacting with serializers, and managing querysets.
    * **ListAPIView:** Designed for retrieving collections of resources, handling HTTP GET requests
        for listing multiple instances of a model, often with pagination and filtering support.
    * **CreateAPIView:** Handles HTTP POST requests for creating new resources, deserializing incoming data,
        validating it, and saving new model instances.
    * **RetrieveAPIView:** Processes HTTP GET requests for fetching a single resource instance,
        typically identified by a primary key or unique identifier.
    * **UpdateAPIView:** Supports HTTP PUT (full update) and PATCH (partial update) requests for
        modifying existing resources.
    * **DestroyAPIView:** Handles HTTP DELETE requests for removing existing resource instances.
    * **ListCreateAPIView:** A composite view combining listing (GET) and creation (POST) functionalities
        on the same endpoint.
    * **RetrieveUpdateDestroyAPIView:** A comprehensive view for single-resource management,
        combining retrieval (GET), updating (PUT/PATCH), and deletion (DELETE).

3.  **Mixins (from .mixins):**
    Reusable classes that provide specific behaviors to generic views, allowing for flexible composition
    of API functionalities. These mixins encapsulate common logic for model operations.

    * **ListModelMixin:** Provides logic for listing a queryset of model instances.
    * **CreateModelMixin:** Provides logic for creating a new model instance.
    * **RetrieveModelMixin:** Provides logic for retrieving a single model instance.
    * **UpdateModelMixin:** Provides logic for updating an existing model instance.
    * **DestroyModelMixin:** Provides logic for deleting a model instance.

4.  **Serializers (from .serializer):**
    Essential components for data serialization and deserialization. They are crucial for converting
    complex data types (like model instances) into formats suitable for API responses (e.g., JSON)
    and converting incoming data back into model instances for processing.

    * **Field:** The base class for all serializer fields, defining common behavior for data representation,
        validation, and conversion.
    * **BooleanField:** A serializer field for handling boolean values.
    * **BaseModelSerializer:** The base serializer class designed for integration with Lback's models,
        simplifying conversion between model instances and serializable data structures.
    * **IntegerField:** A serializer field for handling integer numbers.
    * **StringField:** A serializer field for handling text-based data (strings).
    * **RelatedField:** A serializer field for representing relationships between different models.
    * **DateTimeField:** A serializer field for handling date and time values, managing conversion
        to and from various string formats.

5.  **View Classes (from .view):**
    Fundamental view classes that serve as the entry points for handling web requests within the Lback framework.

    * **APIView:** The primary base class for defining API views, providing a robust foundation for handling
        different HTTP methods and orchestrating the request-response cycle for API endpoints.
    * **BaseView:** A more general-purpose base view class that might serve as a fundamental building block
        for views not strictly adhering to REST principles, or for traditional web page rendering.
"""
