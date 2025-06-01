from typing import List,Any

from lback.api.view import APIView
from lback.api.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from lback.core.response import Response

class GenericAPIView(APIView):
    """
    Base class for all generic views.
    Provides context for various generic behaviors.
    """

class ListAPIView(ListModelMixin, GenericAPIView):
    """
    View for listing a queryset.
    """
    def get(self, request: Any, *args, **kwargs) -> List[Any]:
        return self.list(request, *args, **kwargs)

class CreateAPIView(CreateModelMixin, GenericAPIView):
    """
    View for creating a model instance.
    """
    def post(self, request: Any, *args, **kwargs) -> Any:
        return self.create(request, *args, **kwargs)

class RetrieveAPIView(RetrieveModelMixin, GenericAPIView):
    """
    View for retrieving a model instance.
    """
    def get(self, request: Any, *args, **kwargs) -> Any:
        return self.retrieve(request, *args, **kwargs)

class UpdateAPIView(UpdateModelMixin, GenericAPIView):
    """
    View for updating a model instance.
    """
    def put(self, request: Any, *args, **kwargs) -> Any:
        return self.update(request, *args, **kwargs)
    
    def patch(self, request: Any, *args, **kwargs) -> Any:
        return self.update(request, *args, **kwargs)

class DestroyAPIView(DestroyModelMixin, GenericAPIView):
    """
    View for deleting a model instance.
    """
    def delete(self, request: Any, *args, **kwargs) -> Response:
        return self.destroy(request, *args, **kwargs)
    
class ListCreateAPIView(ListModelMixin, CreateModelMixin, GenericAPIView):
    """
    View for listing and creating model instances.
    """
    def get(self, request: Any, *args, **kwargs) -> List[Any]: return self.list(request, *args, **kwargs)
    def post(self, request: Any, *args, **kwargs) -> Any: return self.create(request, *args, **kwargs)

class RetrieveUpdateDestroyAPIView(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):
    """
    View for retrieving, updating, and deleting a model instance.
    """
    def get(self, request: Any, *args, **kwargs) -> Any: return self.retrieve(request, *args, **kwargs)
    def put(self, request: Any, *args, **kwargs) -> Any: return self.update(request, *args, **kwargs)
    def patch(self, request: Any, *args, **kwargs) -> Any: return self.update(request, *args, **kwargs)
    def delete(self, request: Any, *args, **kwargs) -> Response: return self.destroy(request, *args, **kwargs)