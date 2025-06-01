import logging
import json
from typing import Any, List, Optional, Callable, Dict, Type
from http import HTTPStatus

from lback.core.signals import dispatcher
from lback.core.exceptions import MethodNotAllowed, NotFound
from lback.core.response import Response
from lback.models.base import BaseModel
from lback.api.serializer import BaseModelSerializer

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)

class BaseView:
    """
    Base class for all view handlers in the framework.
    Provides basic dispatching logic.
    Integrates SignalDispatcher to emit events during request dispatching.
    """
    methods: Optional[List[str]] = None

    def dispatch(self, request: Any, *args, **kwargs) -> Any:
        """
        Dispatches the incoming request to the appropriate HTTP method handler.
        Emits 'view_dispatch_started', 'view_dispatch_succeeded', 'view_method_not_allowed',
        or 'view_handler_not_implemented' signals.

        Args:
            request: The incoming request object (already processed by middleware).
            *args: Positional arguments extracted from the URL path.
            **kwargs: Keyword arguments extracted from the URL path.

        Returns:
            The result of calling the specific method handler (e.g., self.get, self.post).
            This result is typically a Response object or data to be converted to a Response.

        Raises:
            MethodNotAllowed: If the request method is not in self.methods.
                              (Although the Router should ideally catch this first).
            NotImplementedError: If a method is allowed but no handler method is defined.
            Any exception raised by the specific method handler.
        """
        view_name = self.__class__.__name__
        request_method = request.method.upper()
        request_path = getattr(request, 'path', 'N/A') 

        logger.debug(f"Dispatching request method '{request_method}' for path '{request_path}' to view {view_name}.")

        dispatcher.send("view_dispatch_started", sender=self, view_instance=self, request=request, method=request_method, path=request_path)
        logger.debug(f"Signal 'view_dispatch_started' sent for {view_name}, method '{request_method}', path '{request_path}'.")


        if self.methods is not None and request_method not in self.methods:
             logger.warning(f"Method '{request_method}' not allowed by view {view_name}. Allowed: {self.methods}")

             dispatcher.send("view_method_not_allowed", sender=self, view_instance=self, request=request, method=request_method, path=request_path, allowed_methods=self.methods)
             logger.debug(f"Signal 'view_method_not_allowed' sent for {view_name}, method '{request_method}'.")
             raise MethodNotAllowed(path=request_path, method=request_method, allowed_methods=self.methods)

        handler_name = request_method.lower()
        handler: Optional[Callable] = getattr(self, handler_name, None)

        if handler is None or not callable(handler):
             logger.error(f"View {view_name} has no callable handler method '{handler_name}' for method '{request_method}'.")

             dispatcher.send("view_handler_not_implemented", sender=self, view_instance=self, request=request, method=request_method, path=request_path, handler_name=handler_name)
             logger.debug(f"Signal 'view_handler_not_implemented' sent for {view_name}, method '{request_method}'.")
             raise NotImplementedError(f"Handler method '{handler_name}' not implemented for view {view_name}.")

        try:
            logger.debug(f"Calling handler method {view_name}.{handler_name} for {request_method} {request_path}")
            response = handler(request, *args, **kwargs)

            logger.debug(f"Handler method {view_name}.{handler_name} completed.")

            dispatcher.send("view_dispatch_succeeded", sender=self, view_instance=self, request=request, method=request_method, path=request_path, response=response)
            logger.debug(f"Signal 'view_dispatch_succeeded' sent for {view_name}, method '{request_method}'.")

            return response

        except Exception as e:

            logger.exception(f"Exception raised by handler method {view_name}.{handler_name} for {request_method} {request_path}: {e}")
            raise 

class APIView(BaseView):
    """
    Base class for API views, providing common functionalities like:
    - Default allowed HTTP methods.
    - Automatic request body parsing (JSON).
    - Automatic response serialization to JSON.
    - Basic object/queryset retrieval logic (requires `model` and `serializer_class`).
    - Standardized error responses.
    """
    methods: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

    model: Optional[Type[BaseModel]] = None
    serializer_class: Optional[Type[BaseModelSerializer]] = None
    

    def dispatch(self, request: Any, *args, **kwargs) -> Response:

        self.request = request
        self.kwargs = kwargs
        
        self.parsed_request_data: Dict[str, Any] = {}
        if request.method in ["POST", "PUT", "PATCH"]:

            try:
                self.parsed_request_data = request.parsed_body if hasattr(request, 'parsed_body') and request.parsed_body is not None else {}
            except json.JSONDecodeError:
                return Response(json.dumps({"detail": "Invalid JSON in request body"}), 
                                status=HTTPStatus.BAD_REQUEST.value, 
                                content_type="application/json")
        
        try:
            response_data = super().dispatch(request, *args, **kwargs)

            if not isinstance(response_data, Response):
                return self._serialize_response(response_data)
            return response_data 

        except MethodNotAllowed as e:
            logger.warning(f"Method not allowed for {request.path}: {e.method} not in {e.allowed_methods}")
            return Response(json.dumps({"detail": f"Method {e.method} not allowed. Allowed methods: {', '.join(e.allowed_methods)}"}), 
                            status=HTTPStatus.METHOD_NOT_ALLOWED.value, 
                            content_type="application/json")
        
        except NotFound as e:
            logger.warning(f"Resource not found for {request.path}: {e.message}")
            return Response(json.dumps({"detail": e.message}), 
                            status=HTTPStatus.NOT_FOUND.value, 
                            content_type="application/json")
        
        except NotImplementedError as e:
            logger.error(f"API Method not implemented: {e}")
            return Response(json.dumps({"detail": "This API method is not implemented."}), 
                            status=HTTPStatus.NOT_IMPLEMENTED.value, 
                            content_type="application/json")
        
        except Exception as e:
            logger.exception(f"Unhandled exception in APIView dispatch for {request.path}: {e}")
            return Response(json.dumps({"detail": "An unexpected server error occurred."}), 
                            status=HTTPStatus.INTERNAL_SERVER_ERROR.value, 
                            content_type="application/json")

    def _serialize_response(self, data: Any) -> Response:
        """
        Serializes the given data to a JSON Response using the specified serializer_class.

        If serializer_class is not defined, attempts to serialize the data directly to JSON.
        Handles both single objects and lists of objects.

        Args:
            data (Any): The data to be serialized and returned in the response.

        Returns:
            Response: A Response object containing the serialized data as JSON.

        Raises:
            TypeError: If the data cannot be serialized to JSON and no serializer_class is defined.
        """
        if self.serializer_class is None:
            logger.warning(f"APIView {self.__class__.__name__} returned data but no serializer_class is defined. Returning raw JSON.")
            try:
                return Response(json.dumps(data), content_type="application/json", status=HTTPStatus.OK.value)
            except TypeError:
                return Response(json.dumps({"detail": "Data could not be serialized to JSON without a serializer_class."}), 
                                status=HTTPStatus.INTERNAL_SERVER_ERROR.value, 
                                content_type="application/json")
        

        if isinstance(data, list):
            serialized_data = [self.serializer_class(obj).data for obj in data]

        else:
            serialized_data = self.serializer_class(data).data
            
        return Response(json.dumps(serialized_data), content_type="application/json", status=HTTPStatus.OK.value)

    def get_serializer(self, instance: Any = None, data: Optional[Dict[str, Any]] = None, **kwargs) -> BaseModelSerializer:
        """
        Returns an instance of the serializer specified for this view.

        Args:
            instance (Any, optional): The model instance to serialize.
            data (dict, optional): Data to be deserialized and validated.
            **kwargs: Additional keyword arguments for the serializer.

        Returns:
            BaseModelSerializer: An instance of the serializer class.

        Raises:
            NotImplementedError: If serializer_class is not defined.
        """
        if self.serializer_class is None:
            raise NotImplementedError("serializer_class must be defined for APIView.")
        
        return self.serializer_class(instance=instance, data=data, **kwargs)

    def get_queryset(self):
        """
        Returns the base QuerySet for the specified model.

        Returns:
            QuerySet: The QuerySet for the model.

        Raises:
            NotImplementedError: If model is not defined.
            Exception: If the database session is not available.
        """
        if self.model is None:
            raise NotImplementedError(f"Model must be defined for APIView {self.__class__.__name__}.")
        
        db_session = self.request.db_session
        if not db_session:
            raise Exception("Database session is not available.")
        return db_session.query(self.model)

    def get_object(self):
        """
        Retrieves a single object based on the ID provided in the URL kwargs.

        Returns:
            Any: The model instance corresponding to the provided primary key.

        Raises:
            NotFound: If the primary key is not found in the URL or the object does not exist.
        """
        pk = self.kwargs.get('object_id')
        if not pk:
            raise NotFound(message="Primary key (object_id) not found in URL path.")
        
        obj = self.get_queryset().get(pk)
        if obj is None:
            raise NotFound(message=f"{self.model.__name__} with ID {pk} not found.")
        
        return obj

    def get(self, request: Any, *args, **kwargs) -> Any: raise NotImplementedError
    def post(self, request: Any, *args, **kwargs) -> Any: raise NotImplementedError
    def put(self, request: Any, *args, **kwargs) -> Any: raise NotImplementedError
    def patch(self, request: Any, *args, **kwargs) -> Any: raise NotImplementedError
    def delete(self, request: Any, *args, **kwargs) -> Any: raise NotImplementedError
    def options(self, request: Any, *args, **kwargs) -> Any: return Response("", status=HTTPStatus.NO_CONTENT.value)
    def head(self, request: Any, *args, **kwargs) -> Any: return Response("", status=HTTPStatus.NO_CONTENT.value)