from typing import Any, List
import json
from http import HTTPStatus

from lback.core.response import Response
from lback.core.exceptions import ValidationError


class ListModelMixin:
    """
    Mixins لـ List API: Handles listing a queryset of objects.
    Requires the view to have `model` and `serializer_class` defined.
    """
    def list(self, request: Any, *args, **kwargs) -> List[Any]:
        queryset = self.get_queryset()
        objects = queryset.all()
        return objects

class CreateModelMixin:
    """
    Mixins لـ Create API: Handles creating a new object.
    Requires the view to have `model` and `serializer_class` defined.
    """
    def create(self, request: Any, *args, **kwargs) -> Any:
        serializer = self.get_serializer(data=self.parsed_request_data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        
        instance = serializer.save()
        return Response(json.dumps(serializer.data), status=HTTPStatus.CREATED.value, content_type="application/json")


class RetrieveModelMixin:
    """
    Mixins لـ Retrieve API: Handles retrieving a single object by its primary key.
    Requires the view to have `model` and `serializer_class` defined.
    """
    def retrieve(self, request: Any, *args, **kwargs) -> Any:
        obj = self.get_object()
        return obj

class UpdateModelMixin:
    """
    Mixins لـ Update API: Handles updating an existing object (both PUT and PATCH).
    Requires the view to have `model` and `serializer_class` defined.
    """
    def update(self, request: Any, *args, **kwargs) -> Any:
        obj = self.get_object()
        serializer = self.get_serializer(instance=obj, data=self.parsed_request_data, partial=request.method == "PATCH")
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        
        instance = serializer.save()
        return instance

class DestroyModelMixin:
    """
    Mixins لـ Destroy API: Handles deleting an existing object.
    Requires the view to have `model` defined.
    """
    def destroy(self, request: Any, *args, **kwargs) -> Response:
        obj = self.get_object()
        db_session = request.db_session
        if not db_session: raise Exception("DB session not available.")
        
        db_session.delete(obj)
        db_session.commit()
        return Response(status=HTTPStatus.NO_CONTENT.value)