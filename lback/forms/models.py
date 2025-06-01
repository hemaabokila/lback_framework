import logging
from typing import Dict, Any, Optional, Type

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import inspect, Column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import String, Integer, Boolean, Date, DateTime, Time, Float, Numeric, LargeBinary

from .forms import Form, FormMetaclass
from .fields import Field, CharField, IntegerField, BooleanField, FileField
from .fields_datetime import DateField, TimeField, DateTimeField
from .widgets import Widget, TextInput, Textarea, CheckboxInput, FileInput
from .widgets_datetime import DateInput, TimeInput, DateTimeInput


logger = logging.getLogger(__name__)

class ModelFormMetaclass(FormMetaclass):
    """
    Metaclass for ModelForm classes.
    Collects declared fields and automatically generates fields from the associated model.
    """
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        if hasattr(new_class, 'Meta') and hasattr(new_class.Meta, 'model'):
            model = new_class.Meta.model
            if not (isinstance(model, type) and hasattr(model, '__mapper__')):
                 logger.error(f"ModelForm '{name}': Meta.model must be a SQLAlchemy mapped class (have a __mapper__ attribute), but got {type(model)}.")
                 raise TypeError(f"ModelForm '{name}': Meta.model must be a SQLAlchemy mapped class.")

            meta_fields = getattr(new_class.Meta, 'fields', None)
            meta_exclude = getattr(new_class.Meta, 'exclude', None)
            meta_widgets = getattr(new_class.Meta, 'widgets', {})
            meta_field_classes = getattr(new_class.Meta, 'field_classes', {})
            meta_localized_fields = getattr(new_class.Meta, 'localized_fields', None)

            mapper = inspect(model)
            model_fields = {}
            for column in mapper.columns:
                model_fields[column.name] = column


            fields_to_include = []
            if meta_fields is not None:
                fields_to_include = meta_fields
            else:
                fields_to_include = list(model_fields.keys())
                if meta_exclude is not None:
                    fields_to_include = [name for name in fields_to_include if name not in meta_exclude]

            generated_fields = {}
            for field_name in fields_to_include:
                if field_name in new_class._declared_fields:
                    declared_field = new_class._declared_fields[field_name]
                    if declared_field.name is None:
                         declared_field.name = field_name
                    generated_fields[field_name] = declared_field
                    logger.debug(f"ModelForm '{name}': Using explicitly declared field '{field_name}'.")
                elif field_name in model_fields:
                    model_column = model_fields[field_name]
                    form_field = cls._get_form_field_for_column(model_column, meta_widgets.get(field_name), meta_field_classes.get(field_name))
                    if form_field:
                        form_field.name = field_name
                        form_field.label = form_field.label or field_name.replace('_', ' ').title()
                        form_field.required = not model_column.nullable
                        if isinstance(form_field, CharField) and hasattr(model_column.type, 'length'):
                             form_field.max_length = model_column.type.length

                        generated_fields[field_name] = form_field
                        logger.debug(f"ModelForm '{name}': Generated field '{field_name}' from model column.")
                    else:
                        logger.warning(f"ModelForm '{name}': Could not generate form field for model column '{field_name}' with type {type(model_column.type)}. Skipping.")
                else:
                    logger.warning(f"ModelForm '{name}': Field '{field_name}' specified in Meta.fields but not found in model or as declared field. Skipping.")

            for field_name, generated_field_instance in generated_fields.items():
                 if field_name not in new_class._declared_fields:
                     new_class._declared_fields[field_name] = generated_field_instance
                     logger.debug(f"ModelForm '{name}': Added generated field '{field_name}' to _declared_fields.")
                 else:
                     logger.debug(f"ModelForm '{name}': Generated field '{field_name}' was already present in _declared_fields (explicitly declared or from base).")


        logger.debug(f"ModelFormMetaclass: Final declared fields for '{name}': {list(new_class._declared_fields.keys())}")

        return new_class

    @classmethod
    def _get_form_field_for_column(
        cls,
        column: Column,
        widget: Optional[Widget] = None,
        field_class: Optional[Type[Field]] = None
    ) -> Optional[Field]:
        """
        Maps a SQLAlchemy column to an appropriate Form Field instance.
        Allows overriding widget and field class.
        """
        if field_class:
             try:
                 return field_class(widget=widget)
             except Exception as e:
                 logger.error(f"ModelFormMetaclass: Error instantiating custom field class {field_class.__name__} for column {column.name}: {e}", exc_info=True)
                 return None


        if isinstance(column.type, String):
            default_widget = Textarea if (column.type.length is not None and column.type.length > 255) else TextInput
            return CharField(widget=widget if widget else default_widget())
        
        elif isinstance(column.type, Integer):
            return IntegerField(widget=widget if widget else TextInput())
        
        elif isinstance(column.type, Boolean):
            return BooleanField(widget=widget if widget else CheckboxInput(), required=not column.nullable)
        
        elif isinstance(column.type, Date):
             return DateField(widget=widget if widget else DateInput())
        
        elif isinstance(column.type, Time):
             return TimeField(widget=widget if widget else TimeInput())
        
        elif isinstance(column.type, DateTime):
             return DateTimeField(widget=widget if widget else DateTimeInput())
        
        elif isinstance(column.type, (Float, Numeric)):
             logger.warning(f"ModelFormMetaclass: Mapping for SQLAlchemy type {type(column.type).__name__} (column '{column.name}') to a form field is not fully implemented. Consider adding FloatField/DecimalField.")
             return None
        
        elif isinstance(column.type, LargeBinary):
             return FileField(widget=widget if widget else FileInput(), required=not column.nullable)

        logger.warning(f"ModelFormMetaclass: No specific form field mapping found for SQLAlchemy column '{column.name}' with type {type(column.type).__name__}. Skipping.")
        return None




class ModelForm(Form, metaclass=ModelFormMetaclass):
    """
    A Form that is automatically generated from a database model.
    Requires a 'Meta' inner class with a 'model' attribute.
    """

    def __init__(
        self,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        initial: Optional[Dict[str, Any]] = None,
        instance: Optional[Any] = None,
    ):
        """
        Initializes a ModelForm instance.
        """
        self.instance = instance

        if self.instance:
             instance_initial_data = self._get_initial_data_from_instance(self.instance)
             if initial:
                  instance_initial_data.update(initial)
             initial = instance_initial_data

        super().__init__(data=data, files=files, initial=initial)

    def _get_initial_data_from_instance(self, instance: Any) -> Dict[str, Any]:
        """
        Extracts initial data for form fields from a model instance.
        """
        initial_data = {}
        for name, field in self.fields.items():
            if hasattr(instance, name):
                value = getattr(instance, name)
                initial_data[name] = value
                logger.debug(f"ModelForm: Extracted initial data for field '{name}' from instance.")
            else:
                logger.warning(f"ModelForm: Instance does not have attribute '{name}' corresponding to a form field.")

        return initial_data


    def save(self, db_session: DBSession, commit: bool = True) -> Any:
        """
        Creates or updates a model instance using the form's cleaned data.
        """
        if not self.is_bound:
            raise ValueError("Cannot save an unbound form.")
        if not self.is_valid():
            error_messages = self.errors
            formatted_errors = "\n".join([f"  {name}: {[str(e) for e in error_list]}" for name, error_list in error_messages.items()])
            logger.error(f"ModelForm.save: Cannot save invalid form. Errors:\n{formatted_errors}")
            raise ValueError(f"Cannot save an invalid form. Errors:\n{formatted_errors}")

        model = self.Meta.model
        if model is None:
             raise RuntimeError("ModelForm Meta.model is not set.")

        cleaned_data = self.cleaned_data

        try:
            if self.instance:
                logger.debug(f"ModelForm.save: Updating existing instance of {model.__name__} with cleaned data.")
                for name, value in cleaned_data.items():
                    setattr(self.instance, name, value)
                saved_instance = self.instance
            else:
                logger.debug(f"ModelForm.save: Creating new instance of {model.__name__} with cleaned data.")
                model_column_names = {c.name for c in inspect(model).columns}
                data_for_model_creation = {k: v for k, v in cleaned_data.items() if k in model_column_names}

                for field_name, value in cleaned_data.items():
                    if isinstance(self.fields.get(field_name), FileField) and field_name in model_column_names:
                         mapper = inspect(model)
                         model_column = mapper.columns.get(field_name)
                         if model_column and isinstance(model_column.type, LargeBinary):
                             if value is not None and hasattr(value, 'read'):
                                 try:
                                     if hasattr(value, 'seek') and callable(value.seek):
                                         value.seek(0)
                                     file_content = value.read()
                                     data_for_model_creation[field_name] = file_content
                                     logger.debug(f"ModelForm.save: Read file content for field '{field_name}'.")
                                 except Exception as file_read_e:
                                     logger.error(f"ModelForm.save: Error reading file content for field '{field_name}': {file_read_e}", exc_info=True)
                                     raise ValueError(f"Error reading file for {field_name}") from file_read_e
                             else:
                                 data_for_model_creation[field_name] = None if model_column.nullable else b''
                                 logger.debug(f"ModelForm.save: No file uploaded for field '{field_name}'. Setting model attribute to None/empty bytes.")


                saved_instance = model(**data_for_model_creation)
                db_session.add(saved_instance)

            if commit:
                logger.debug("ModelForm.save: Committing DB session.")
                db_session.commit()
                logger.debug("ModelForm.save: DB session committed.")
            else:
                 db_session.flush()
                 logger.debug("ModelForm.save: DB session flushed (commit=False).")


            logger.info(f"ModelForm.save: Successfully saved instance of {model.__name__}.")
            return saved_instance

        except SQLAlchemyError as e:
            logger.error(f"ModelForm.save: Database error saving instance of {model.__name__}: {e}", exc_info=True)
            raise 
        except Exception as e:
            logger.exception(f"ModelForm.save: Unexpected error saving instance of {model.__name__}: {e}")
            raise

    def clean(self):
        """
        Performs form-level validation that depends on multiple fields.
        Should raise ValidationError for non-field errors.
        Can also modify self.cleaned_data.
        Subclasses should override this method if form-level validation is needed.
        """
        super().clean()
        return self.cleaned_data

