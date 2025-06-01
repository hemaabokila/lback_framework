import logging
from typing import Any, Dict, Optional, List, Type, Union, TypeVar
import datetime

from lback.core.signals import dispatcher
from lback.core.exceptions import ValidationError
from lback.models.base import BaseModel

from sqlalchemy import inspect

logger = logging.getLogger(__name__)

T = TypeVar('T')

class Field:
    """
    Base class for serializer fields.
    Provides methods for data representation, internal value conversion, and validation.
    """
    def __init__(self, required: bool = True, allow_null: bool = False, default: Any = None, help_text: Optional[str] = None, read_only: bool = False):
        self.required = required
        self.allow_null = allow_null
        self.default = default
        self.help_text = help_text
        self.field_name: Optional[str] = None
        self.source: Optional[str] = None
        self.read_only = read_only

    def to_representation(self, value: Any) -> Any:
        """Converts a model field value to its representation for output."""
        return value

    def to_internal_value(self, data: Any) -> Any:
        """Converts input data to its internal value for validation/saving."""
        return data

    def validate(self, value: Any):
        """Performs field-level validation."""
        if self.required and (value is None or (isinstance(value, str) and not value.strip())):
            raise ValidationError(f"The '{self.field_name}' field is required.")
        if not self.allow_null and value is None:
            raise ValidationError(f"The '{self.field_name}' field may not be null.")
        if value is None and self.allow_null:
            return value

    def __set_name__(self, owner, name):
        """Called automatically by Python when the field is defined on a class."""
        self.field_name = name


class DateTimeField(Field):
    """
    A field for handling datetime objects, converting them to/from ISO 8601 strings.
    """
    def __init__(self, format: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.format = format if format is not None else '%Y-%m-%dT%H:%M:%S.%fZ'

    def to_representation(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.isoformat() + ('Z' if value.tzinfo is None else '')
        try:
            return str(value)
        except Exception:
            raise ValidationError(f"Could not represent '{self.field_name}' as datetime string.")

    def to_internal_value(self, data: Any) -> Optional[datetime.datetime]:
        if data is None:
            if not self.allow_null and self.required:
                raise ValidationError(f"The '{self.field_name}' field cannot be null.")
            return None
        
        if isinstance(data, datetime.datetime):
            return data

        if isinstance(data, str):
            try:
                if 'T' in data and '-' in data:
                    if data.endswith('Z'):
                        return datetime.datetime.fromisoformat(data[:-1]).replace(tzinfo=datetime.timezone.utc)
                    return datetime.datetime.fromisoformat(data)
                
                return datetime.datetime.strptime(data, self.format)

            except ValueError:
                raise ValidationError(f"The '{self.field_name}' field must be a valid datetime string (e.g., ISO 8601 format).")
        
        raise ValidationError(f"The '{self.field_name}' field must be a valid datetime string or object.")

    def validate(self, value: Any):
        super().validate(value)
        if value is not None and not isinstance(value, (datetime.datetime, str)):
            raise ValidationError(f"The '{self.field_name}' field must be a datetime object or a valid datetime string.")
        return value

    @property
    def openapi_type(self) -> Dict[str, Any]:
        return {"type": "string", "format": "date-time"}
    
class StringField(Field):
    def __init__(self, max_length: Optional[int] = None, min_length: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
    
    def validate(self, value: Any):
        super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"The '{self.field_name}' field must be a string.")
            if self.max_length is not None and len(value) > self.max_length:
                raise ValidationError(f"The '{self.field_name}' field must be no longer than {self.max_length} characters.")
            if self.min_length is not None and len(value) < self.min_length:
                raise ValidationError(f"The '{self.field_name}' field must be at least {self.min_length} characters.")
        return value

    @property
    def openapi_type(self) -> Dict[str, Any]:
        return {"type": "string"}

class IntegerField(Field):
    def __init__(self, min_value: Optional[int] = None, max_value: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def to_internal_value(self, data: Any) -> Any:
        try:
            return int(data)
        except (ValueError, TypeError):
            raise ValidationError(f"The '{self.field_name}' field must be a valid integer.")

    def validate(self, value: Any):
        super().validate(value)
        if value is not None:
            if not isinstance(value, int):
                raise ValidationError(f"The '{self.field_name}' field must be an integer.")
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(f"The '{self.field_name}' field must be at least {self.min_value}.")
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(f"The '{self.field_name}' field must be no greater than {self.max_value}.")
        return value

    @property
    def openapi_type(self) -> Dict[str, Any]:
        return {"type": "integer", "format": "int64"}

class BooleanField(Field):
    def to_internal_value(self, data: Any) -> Any:
        if isinstance(data, str):
            if data.lower() in ('true', '1', 'yes'): return True
            if data.lower() in ('false', '0', 'no'): return False
        if isinstance(data, (int, float)):
            return bool(data)
        if isinstance(data, bool):
            return data
        raise ValidationError(f"The '{self.field_name}' field must be a valid boolean.")

    def validate(self, value: Any):
        super().validate(value)
        if value is not None and not isinstance(value, bool):
            raise ValidationError(f"The '{self.field_name}' field must be a boolean.")
        return value

    @property
    def openapi_type(self) -> Dict[str, Any]:
        return {"type": "boolean"}


class RelatedField(Field):
    """
    A field for handling relationships to other models.
    Can represent as primary key or nested serializer.
    """
    def __init__(self, serializer_class: Type['BaseModelSerializer'], many: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.serializer_class = serializer_class
        self.many = many

    def to_representation(self, value: Any) -> Any:
        if value is None:
            return None
        if self.many:
            return [self.serializer_class(instance=item, context=self.context).data for item in value]
        return self.serializer_class(instance=value, context=self.context).data
    
    def to_internal_value(self, data: Any) -> Any:

        if self.read_only:
            logger.debug(f"Attempted to provide data for read-only field '{self.field_name}'. Ignoring.")
            return None
            
        if self.many:
            if not isinstance(data, list):
                raise ValidationError(f"'{self.field_name}' expected a list of values.")
            internal_values = []
            for item in data:
                if isinstance(item, dict):
                    if 'id' in item:
                        internal_values.append(item['id'])
                    else:
                        raise ValidationError(f"'{self.field_name}' expected a list of IDs or objects with 'id'.")
                else:
                    internal_values.append(item)
            return internal_values
        else:
            if isinstance(data, dict):
                if 'id' in data:
                    return data['id']
                else:
                    raise ValidationError(f"'{self.field_name}' expected an ID or object with 'id'.")
            return data

    @property
    def openapi_type(self) -> Dict[str, Any]:
        schema_name = self.serializer_class.__name__
        if self.many:
            return {"type": "array", "items": {"$ref": f"#/components/schemas/{schema_name}"}}
        return {"$ref": f"#/components/schemas/{schema_name}"}


class BaseModelSerializer:
    """
    Base serializer class for converting model instances to dictionaries
    and validating/converting dictionaries to model instances.
    Integrates SignalDispatcher to emit events during serialization, validation, and saving.
    """
    _declared_fields: Dict[str, Field]

    class Meta:
        """Inner class for serializer options."""
        model: Type[BaseModel] = None
        fields: Union[List[str], str] = '__all__'
        exclude: List[str] = []
        read_only_fields: List[str] = []
        extra_kwargs: Dict[str, Dict[str, Any]] = {}


    def __init__(self, instance: Any = None, data: Optional[Dict[str, Any]] = None, many: bool = False, partial: bool = False, context: Optional[Dict[str, Any]] = None):
        self.instance = instance
        self._data = data
        self.many = many
        self.partial = partial
        self.context = context or {}
        self._errors: Dict[str, List[str]] = {}
        self._validated_data: Optional[Dict[str, Any]] = None

        self._fields = self.__class__._get_fields() 
        for name, field_obj in self._fields.items():
            field_obj.field_name = name
            if field_obj.source is None:
                field_obj.source = name

        logger.debug(f"Serializer {self.__class__.__name__} initialized. Many: {self.many}, Partial: {self.partial}, Fields: {list(self._fields.keys())}")
        dispatcher.send("serializer_initialized", sender=self, serializer=self, many=self.many, partial=self.partial, context=self.context)
        logger.debug(f"Signal 'serializer_initialized' sent for {self.__class__.__name__}.")

    @classmethod
    def _get_fields(cls) -> Dict[str, Field]:
        """
        Collects fields declared directly on the serializer (e.g., username = StringField())
        and fields inferred from Meta.model.
        """
        fields = {}
        for attr_name in dir(cls):
            attr_value = getattr(cls, attr_name)
            if isinstance(attr_value, Field):
                import copy
                fields[attr_name] = copy.deepcopy(attr_value)


        if hasattr(cls, 'Meta') and hasattr(cls.Meta, 'model') and cls.Meta.model is not None:
            model = cls.Meta.model
            mapper = inspect(model)
            meta_fields = getattr(cls.Meta, 'fields', '__all__')
            exclude_fields = getattr(cls.Meta, 'exclude', [])
            read_only_fields = list(getattr(cls.Meta, 'read_only_fields', []))
            extra_kwargs = getattr(cls.Meta, 'extra_kwargs', {})

            model_field_names: List[str] = []
            if meta_fields == '__all__':
                for col in mapper.columns:
                    model_field_names.append(col.key)
                for rel in mapper.relationships:
                    model_field_names.append(rel.key)
            else:
                model_field_names = meta_fields

            for field_name in model_field_names:
                if field_name in exclude_fields:
                    continue
                if field_name in fields:
                    continue

                field_instance: Optional[Field] = None
                
                if field_name in mapper.columns:
                    col = mapper.columns[field_name]
                    required = not col.nullable
                    if col.primary_key: 
                        if field_name not in read_only_fields:
                            read_only_fields.append(field_name)
                        
                    kwargs_for_field = extra_kwargs.get(field_name, {}).copy()
                    kwargs_for_field['required'] = required

                    if hasattr(col.type, 'python_type'):
                        py_type = col.type.python_type
                        if py_type is str: field_instance = StringField(**kwargs_for_field)
                        elif py_type is int: field_instance = IntegerField(**kwargs_for_field)
                        elif py_type is bool: field_instance = BooleanField(**kwargs_for_field)
                        elif py_type is datetime.datetime: field_instance = DateTimeField(**kwargs_for_field)
                        else: field_instance = StringField(**kwargs_for_field)
                    else:
                        field_instance = StringField(**kwargs_for_field)
                
                elif field_name in mapper.relationships:
                    rel = mapper.relationships[field_name]
                    if field_name not in read_only_fields:
                        read_only_fields.append(field_name)

                    related_serializer_class_name = f"{rel.argument.class_.__name__}Serializer"
                    related_serializer_class = BaseModelSerializer

                    try:
                        related_serializer_class = globals().get(related_serializer_class_name) or locals().get(related_serializer_class_name)
                        if related_serializer_class is None:
                            logger.warning(f"Could not find serializer '{related_serializer_class_name}' for related model '{rel.argument.class_.__name__}'. Using BaseModelSerializer as fallback.")
                            related_serializer_class = BaseModelSerializer
                        elif not issubclass(related_serializer_class, BaseModelSerializer):
                            logger.error(f"'{related_serializer_class_name}' found but is not a subclass of BaseModelSerializer.")
                            related_serializer_class = BaseModelSerializer

                    except NameError:
                        logger.warning(f"Could not find serializer for related model '{rel.argument.class_.__name__}'. Using BaseModelSerializer.")
                        related_serializer_class = BaseModelSerializer
                    except Exception as e:
                        logger.error(f"Error resolving serializer for {field_name}: {e}")
                        related_serializer_class = BaseModelSerializer

                    kwargs_for_field = extra_kwargs.get(field_name, {}).copy()
                    kwargs_for_field['required'] = rel.uselist

                    field_instance = RelatedField(
                        serializer_class=related_serializer_class, 
                        many=rel.uselist, 
                        **kwargs_for_field
                    )
                
                if field_instance:
                    fields[field_name] = field_instance
        
        for field_name in read_only_fields:
            if field_name in fields:
                fields[field_name].read_only = True
                fields[field_name].required = False
            else:
                logger.warning(f"Field '{field_name}' listed in read_only_fields but not found in serializer fields.")

        for field_name, kwargs in extra_kwargs.items():
            if field_name in fields:
                for k, v in kwargs.items():
                    if k != 'read_only' and k != 'required':
                         setattr(fields[field_name], k, v)
                    elif k == 'read_only':
                        fields[field_name].read_only = v
                        if v: fields[field_name].required = False
                    elif k == 'required':
                         fields[field_name].required = v

        return fields

    @property
    def data(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        logger.debug(f"Attempting to serialize instance(s) using {self.__class__.__name__}. Many: {self.many}")

        dispatcher.send("serializer_pre_serialize", sender=self, serializer=self, instance=self.instance, many=self.many)
        logger.debug(f"Signal 'serializer_pre_serialize' sent for {self.__class__.__name__}.")

        serialized_data = None
        try:
            if self.many:
                if not isinstance(self.instance, (list, tuple)):
                    logger.error(f"Serializer {self.__class__.__name__} with many=True expects a list/tuple instance, got {type(self.instance).__name__}.")
                    serialized_data = []
                else:
                    serialized_data = [self._to_representation_single(item) for item in self.instance]
            else:
                serialized_data = self._to_representation_single(self.instance)

            logger.debug(f"Serialization finished for {self.__class__.__name__}. Result type: {type(serialized_data).__name__}.")

            dispatcher.send("serializer_post_serialize", sender=self, serializer=self, serialized_data=serialized_data)
            logger.debug(f"Signal 'serializer_post_serialize' sent for {self.__class__.__name__}.")

            return serialized_data

        except Exception as e:
            logger.exception(f"Unexpected error during serialization in {self.__class__.__name__}: {e}")
            raise

    def _to_representation_single(self, instance: Any) -> Dict[str, Any]:
        if instance is None:
            return {}

        data = {}
        for field_name, field_instance in self._fields.items():
            custom_method_name = f"get_{field_name}"
            custom_method = getattr(self, custom_method_name, None)

            try:
                if custom_method and callable(custom_method):
                    data[field_name] = custom_method(instance)
                    logger.debug(f"Serialized field '{field_name}' using custom method for {self.__class__.__name__}.")
                else:
                    value = getattr(instance, field_instance.source or field_name, None)
                    data[field_name] = field_instance.to_representation(value)
                    logger.debug(f"Serialized field '{field_name}' directly for {self.__class__.__name__}.")
            except AttributeError:
                logger.warning(f"Field '{field_name}' (source: {field_instance.source}) not found on instance {instance} for {self.__class__.__name__}. Setting to None.")
                data[field_name] = None
            except Exception as e:
                logger.error(f"Error processing field '{field_name}' for instance {instance} in {self.__class__.__name__}: {e}", exc_info=True)
                data[field_name] = None
        return data

    @property
    def is_valid(self) -> bool:
        if self._data is not None and self._validated_data is None and not self._errors:
            try:
                self._validated_data = self._run_validation(self._data)
                if not self._errors:
                    dispatcher.send("serializer_validation_succeeded", sender=self, serializer=self, validated_data=self._validated_data)
                    logger.debug(f"Signal 'serializer_validation_succeeded' sent for {self.__class__.__name__}.")
                else:
                    dispatcher.send("serializer_validation_failed", sender=self, serializer=self, errors=self._errors)
                    logger.debug(f"Signal 'serializer_validation_failed' sent for {self.__class__.__name__}.")

            except ValidationError as e:
                self._errors.update(e.errors)
                if not self._errors:
                    self._errors['non_field_errors'] = e.message if e.message else "Validation failed."
                logger.warning(f"Validation failed with ValidationError in {self.__class__.__name__}. Errors: {self._errors}")
                dispatcher.send("serializer_validation_failed", sender=self, serializer=self, errors=self._errors)
                logger.debug(f"Signal 'serializer_validation_failed' sent for {self.__class__.__name__}.")
                self._validated_data = None

            except Exception as e:
                logger.exception(f"Unexpected error during validation in {self.__class__.__name__}: {e}")
                self._errors['non_field_errors'] = ["An unexpected error occurred during validation."]
                dispatcher.send("serializer_validation_failed", sender=self, serializer=self, errors=self._errors, exception=e)
                logger.debug(f"Signal 'serializer_validation_failed' sent for {self.__class__.__name__}.")
                self._validated_data = None

        return not bool(self._errors)

    @property
    def errors(self) -> Dict[str, List[str]]:
        if self._data is not None and self._validated_data is None and not self._errors:
            _ = self.is_valid
        return self._errors

    @property
    def validated_data(self) -> Optional[Dict[str, Any]]:
        if self._data is not None and self._validated_data is None and not self._errors:
            _ = self.is_valid
        return self._validated_data

    def _run_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs validation on the input data.
        Populates self._errors and returns cleaned data.
        Emits 'serializer_validation_started' signal.
        """
        logger.debug(f"Running validation logic for {self.__class__.__name__} with data keys: {list(data.keys())}")

        signal_data = data.copy()
        for sensitive_key in ['password', 'token']:
            if sensitive_key in signal_data:
                signal_data[sensitive_key] = '***'
        dispatcher.send("serializer_validation_started", sender=self, serializer=self, raw_data=signal_data)
        logger.debug(f"Signal 'serializer_validation_started' sent for {self.__class__.__name__}.")

        cleaned_data = {}
        self._errors = {}

        for field_name, field_instance in self._fields.items():
            if field_instance.read_only:
                if self.instance and hasattr(self.instance, field_name):
                    cleaned_data[field_name] = field_instance.to_representation(getattr(self.instance, field_name))
                continue 

            value = data.get(field_name, field_instance.default)
            if self.partial and field_name not in data:
                if self.instance and hasattr(self.instance, field_name):
                    cleaned_data[field_name] = getattr(self.instance, field_name)
                continue

            try:
                field_instance.validate(value)
                internal_value = field_instance.to_internal_value(value)
                custom_validate_method_name = f"validate_{field_name}"
                custom_validate_method = getattr(self, custom_validate_method_name, None)

                if custom_validate_method and callable(custom_validate_method):
                    logger.debug(f"Calling custom validation method '{custom_validate_method_name}' for '{field_name}'.")
                    cleaned_value = custom_validate_method(internal_value)
                    cleaned_data[field_name] = cleaned_value

                else:
                    cleaned_data[field_name] = internal_value
                    logger.debug(f"No custom validation for '{field_name}'. Added internal value to cleaned data.")

            except ValidationError as e:
                if field_name not in self._errors: self._errors[field_name] = []
                error_messages = e.errors.get(field_name, [str(e)]) if isinstance(e.errors, dict) else [str(e)]
                self._errors[field_name].extend(error_messages)
                logger.debug(f"Field validation failed for '{field_name}': {e}")

            except Exception as e:
                logger.error(f"Unexpected error during field processing for '{field_name}': {e}", exc_info=True)
                if field_name not in self._errors: self._errors[field_name] = []
                self._errors[field_name].append(f"An unexpected error occurred during processing: {e}")

        if not self._errors:
            try:
                self._run_object_validation(cleaned_data)

            except ValidationError as e:
                self._errors['non_field_errors'] = e.errors.get('_detail', [str(e)]) if isinstance(e.errors, dict) else [str(e)]
                logger.debug(f"Object-level validation failed: {e}")

            except Exception as e:
                logger.error(f"Unexpected error during object-level validation: {e}", exc_info=True)
                if 'non_field_errors' not in self._errors: self._errors['non_field_errors'] = []
                self._errors['non_field_errors'].append("An unexpected error occurred during object validation.")

        logger.debug(f"Validation logic finished for {self.__class__.__name__}. Errors: {self._errors}")
        return cleaned_data

    def _run_object_validation(self, cleaned_data: Dict[str, Any]):
        """
        Placeholder for object-level validation.
        Subclasses can override this to perform validation that depends on multiple fields.
        Should raise ValidationError if validation fails.
        """
        pass

    def save(self, session: Any) -> Any:
        """
        Creates or updates a model instance using validated data.
        Requires a database session.
        Emits 'serializer_pre_save' and 'serializer_post_save' signals.

        Args:
            session: The database session to use for saving.

        Returns:
            The created or updated model instance.

        Raises:
            ValidationError: If the data is not valid.
            RuntimeError: If validated data is missing unexpectedly.
            NotImplementedError: If the serializer has no associated model_class.
            Exception: For other unexpected errors during the save process.
        """
        logger.debug(f"Attempting to save instance using {self.__class__.__name__}.")

        if not self.is_valid:
            logger.warning(f"Attempted to save {self.__class__.__name__} with invalid data. Errors: {self.errors}")
            raise ValidationError(self.errors)

        validated_data = self.validated_data
        if validated_data is None:
            logger.error(f"Validated data is None for {self.__class__.__name__} after successful validation.")
            raise RuntimeError("Validated data is missing after successful validation.")

        signal_data = validated_data.copy()
        for sensitive_key in ['password', 'token']:
            if sensitive_key in signal_data:
                signal_data[sensitive_key] = '***'

        dispatcher.send("serializer_pre_save", sender=self, serializer=self, validated_data=signal_data, instance=self.instance, session=session)
        logger.debug(f"Signal 'serializer_pre_save' sent for {self.__class__.__name__}.")

        instance = self.instance

        try:
            model_class = self.Meta.model
            if model_class is None:
                logger.error(f"Serializer {self.__class__.__name__} has no associated model_class defined in Meta for saving.")
                raise NotImplementedError(f"Saving not implemented: no model_class defined in Meta for {self.__class__.__name__}.")
            
            data_to_save = {}
            for k, v in validated_data.items():
                field_obj = self._fields.get(k)
                if field_obj and field_obj.read_only:
                    continue
                data_to_save[k] = v

            if instance is None:
                logger.debug(f"Creating new instance using {self.__class__.__name__}.")
                instance = model_class(**data_to_save)
                session.add(instance)
                logger.info(f"New instance of {model_class.__name__} created and added to session via {self.__class__.__name__}.")

            else:
                logger.debug(f"Updating existing instance {instance} using {self.__class__.__name__}.")
                for key, value in data_to_save.items():
                    if key == 'password' and hasattr(instance, 'set_password') and callable(instance.set_password):
                        instance.set_password(value)
                        logger.debug(f"Updated password for {instance.__class__.__name__} via set_password method.")
                    elif hasattr(instance, key):
                        setattr(instance, key, value)
                        logger.debug(f"Updated attribute '{key}' for {instance.__class__.__name__}.")
                    else:
                        logger.warning(f"Attempted to set non-existent or ignored attribute '{key}' on instance {instance} during update via {self.__class__.__name__}. Value: {value}")

            session.commit()
            self.instance = instance
            logger.debug(f"Save operation finished for {self.__class__.__name__}.")

            dispatcher.send("serializer_post_save", sender=self, serializer=self, instance=instance, session=session)
            logger.debug(f"Signal 'serializer_post_save' sent for {self.__class__.__name__}.")

            return instance

        except NotImplementedError:
            raise
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error during save operation in {self.__class__.__name__}: {e}", exc_info=True)
            raise