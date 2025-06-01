import logging
import json
from typing import Dict, Any, Optional, Type, List, Union
from http import HTTPStatus
from datetime import datetime, date
import os
from urllib.parse import urljoin
from werkzeug.datastructures import MultiDict 

from sqlalchemy import inspect, or_, and_, asc, desc
from sqlalchemy.orm import RelationshipProperty, Query, ColumnProperty
from sqlalchemy.types import JSON, String, Integer, DateTime, Boolean, Text, Date, Float, Numeric
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import Session as SQLASession

from lback.core.response import Response
from lback.core.types import Request, HTTPMethod, UploadedFile
from lback.models.base import BaseModel
from lback.models.adminuser import AdminUser

from lback.core.config import Config
from lback.utils.shortcuts import render, redirect, return_404, return_500, get_model_form_data, paginate_query
from lback.utils.file_handlers import save_uploaded_file, delete_saved_file, validate_uploaded_file
from lback.auth.permissions import PermissionRequired

logger = logging.getLogger(__name__)


@PermissionRequired(lambda request: f"add_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "add_unknown_model")
def generic_add_view(request: Request, model: Type[BaseModel]) -> Response:
    """
    Handles the generic "add" view for creating new instances of a database model.

    This view supports both displaying an empty form for new object creation (GET request)
    and processing form submissions to persist a new object to the database (POST request).
    It dynamically handles various SQLAlchemy column types and relationships (Many-to-One,
    One-to-One, Many-to-Many) based on the provided model's schema.

    It includes:
    - Dynamic permission checking using the `@PermissionRequired` decorator.
    - Handling of file uploads with configurable allowed types and max size.
    - Type conversion for different database column types (String, Integer, Boolean, DateTime, JSON).
    - Error handling for form validation and database integrity issues.
    - Redirection upon successful creation or re-rendering the form with errors.

    :param request: The incoming request object, containing parsed body, files,
                    database session, configuration, and router information.
    :type request: Request
    :param model: The SQLAlchemy `BaseModel` class for which a new instance is to be added.
    :type model: Type[BaseModel]
    :returns: A `Response` object, either a redirect on success, or a rendered form
              (potentially with errors) on failure or for initial display.
    :rtype: Response
    """
    model_name = getattr(model, '__name__', 'UnknownModel')
    logger.info(f"Handling generic add view for model: {model_name}, Method: {request.method} for {request.path}.")

    db_session: Optional[SQLASession] = request.db_session
    config: Optional[Config] = request.config
    router: Any = request.router
    if not hasattr(request, '_context') or request._context is None:
        request._context = {}

    if 'form_errors' not in request._context:
        request._context['form_errors'] = {}

    if not all([db_session, config, router]):
        logger.critical(f"Generic Add View for {model_name}: Missing required dependencies on request (db_session, config, router).")
        return return_500(request, message="Internal Server Error: Missing dependencies.")

    template_name = f'admin/generic_form.html'

    if request.method == HTTPMethod.POST:
        logger.info(f"Generic Add View for {model_name}: Processing POST request.")
        form_data: MultiDict = request.parsed_body if isinstance(request.parsed_body, MultiDict) else MultiDict()
        uploaded_files: MultiDict = request.files if isinstance(request.files, MultiDict) else MultiDict()

        new_obj = model()
        mapper = inspect(model)
        all_model_attributes = {attr.key: attr for attr in mapper.attrs}

        fields_to_process_later: Dict[str, Any] = {}

        for field_name, attr in all_model_attributes.items():
            excluded_fields = ['id', 'created_at', 'updated_at', 'published_at', 'password', 'is_superuser', 'role_id', 'csrfmiddlewaretoken', 'slug']
            if field_name in excluded_fields:
                continue

            if isinstance(attr, ColumnProperty): 
                column = attr.columns[0]
                is_file_field = isinstance(column.type, (String, Text)) and (field_name.endswith('_file') or field_name.endswith('_path'))

                if is_file_field:
                    if field_name in uploaded_files:
                        uploaded_file_object: Union[UploadedFile, List[UploadedFile]] = uploaded_files[field_name]
                        if isinstance(uploaded_file_object, list):
                            if uploaded_file_object:
                                uploaded_file_object = uploaded_file_object[0]
                                logger.warning(f"Generic Add View for {model_name}: Multiple files uploaded for '{field_name}'. Processing only the first one.")
                            else:
                                uploaded_file_object = None
                        if isinstance(uploaded_file_object, UploadedFile):
                            logger.debug(f"Generic Add View for {model_name}: Found uploaded file for '{field_name}': {uploaded_file_object.filename}")
                            allowed_types = getattr(config, 'UPLOAD_ALLOWED_TYPES', None)
                            max_size_mb = getattr(config, 'UPLOAD_MAX_SIZE_MB', None)
                            saved_file_path = save_uploaded_file(uploaded_file_object, config, model_name,
                                                                 allowed_types=allowed_types, max_size_mb=max_size_mb)
                            if saved_file_path:
                                setattr(new_obj, field_name, saved_file_path)
                                logger.info(f"Generic Add View for {model_name}: Assigned saved file path '{saved_file_path}' to field '{field_name}'.")
                            else:
                                validation_error_msg = validate_uploaded_file(uploaded_file_object, allowed_types, max_size_mb)
                                if validation_error_msg:
                                    request._context['form_errors'][field_name] = validation_error_msg
                                    logger.warning(f"Generic Add View for {model_name}: File validation failed for '{field_name}': {validation_error_msg}")
                                else:
                                    request._context['form_errors'][field_name] = 'Failed to upload file.'
                                    logger.error(f"Generic Add View for {model_name}: Failed to save uploaded file for '{field_name}' without specific validation error.")
                        elif uploaded_file_object is not None:
                             logger.warning(f"Generic Add View for {model_name}: Unexpected type for uploaded file '{field_name}': {type(uploaded_file_object)}. Skipping file processing.")
                             request._context['form_errors'][field_name] = 'Invalid file format received.'

                else: 
                    if field_name in form_data:
                        value = form_data.get(field_name) 
                        
                        if isinstance(value, list) and value: 
                            value = value[0]
                        if isinstance(column.type, (String, Text)):
                            setattr(new_obj, field_name, value)
                        elif isinstance(column.type, Integer):
                            try:
                                if value == '' and column.nullable:
                                    setattr(new_obj, field_name, None)
                                else:
                                    setattr(new_obj, field_name, int(value))
                            except (ValueError, TypeError):
                                logger.warning(f"Generic Add View for {model_name}: Invalid integer value '{value}' for field '{field_name}'.")
                                request.add_context('form_errors', {field_name: 'Invalid integer value.'})
                                setattr(new_obj, field_name, None if column.nullable else 0)

                        elif isinstance(column.type, Boolean):
                            setattr(new_obj, field_name, value == 'on')

                        elif isinstance(column.type, DateTime):
                            try:
                                if value == '' and column.nullable:
                                    setattr(new_obj, field_name, None)
                                else:
                                    setattr(new_obj, field_name, datetime.fromisoformat(value) if value else None)

                            except (ValueError, TypeError):
                                logger.warning(f"Generic Add View for {model_name}: Invalid datetime value '{value}' for field '{field_name}'.")
                                request.add_context('form_errors', {field_name: 'Invalid datetime value.'})
                                setattr(new_obj, field_name, None if column.nullable else datetime.utcnow())

                        elif isinstance(column.type, JSON):
                            try:
                                if value == '' and column.nullable:
                                    setattr(new_obj, field_name, None)
                                    
                                else:
                                    setattr(new_obj, field_name, json.loads(value))

                            except (json.JSONDecodeError, TypeError):
                                logger.warning(f"Generic Add View for {model_name}: Invalid JSON value for field '{field_name}'.")
                                request.add_context('form_errors', {field_name: 'Invalid JSON value.'})
                                setattr(new_obj, field_name, None if column.nullable else {})
                        else:
                            setattr(new_obj, field_name, value)

            elif isinstance(attr, RelationshipProperty):
                relation_type = attr.direction.name.lower()
                
                if relation_type in ('manytoone', 'onetoone'):
                    fk_column_name = None
                    if attr.local_remote_pairs:
                        fk_column_name = attr.local_remote_pairs[0][0].name
                    if fk_column_name and fk_column_name in form_data:
                        fk_value = form_data.get(fk_column_name)
                        if isinstance(fk_value, list) and fk_value:
                            fk_value = fk_value[0]
                        fields_to_process_later[fk_column_name] = {'type': relation_type, 'value': fk_value, 'attr': attr}

                    elif fk_column_name and attr.local_remote_pairs[0][0].nullable:
                        fields_to_process_later[fk_column_name] = {'type': relation_type, 'value': None, 'attr': attr}

                    elif fk_column_name:
                         logger.warning(f"Generic Add View for {model_name}: Required FK field '{fk_column_name}' not provided.")
                         request.add_context('form_errors', {fk_column_name: 'This field is required.'})

                elif relation_type == 'manytomany':
                    form_field_name_in_html = field_name 
                    received_values = form_data.getlist(f"{form_field_name_in_html}[]")
                    
                    if not received_values:
                        received_values = form_data.getlist(form_field_name_in_html)

                    cleaned_ids = []
                    for item in received_values: 
                        if item is not None and str(item).strip() != '':
                            try:
                                cleaned_ids.append(int(item))
                            except ValueError:
                                logger.warning(f"Generic Add View: Invalid ID format for M2M '{form_field_name_in_html}': {item}. Skipping.")
                    
                    fields_to_process_later[field_name] = {'type': relation_type, 'value': cleaned_ids, 'attr': attr}

        form_errors = request.get_context('form_errors', {})
        if form_errors:
             logger.warning(f"Generic Add View for {model_name}: Form errors detected before initial save attempt. Not attempting to save.")
             mapper = inspect(model)
             form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, new_obj)

             context = {
                 'model_name': model_name,
                 'is_add': True,
                 'form_fields_data': form_fields_data,
                 'relationship_fields_data': relationship_fields_data,
                 'object': new_obj,
                 'form_errors': form_errors,
                 'error_message': "Please correct the errors below.",
                 'admin_base_template': 'admin/base.html',
                 'router': router,
                 'config': config,
                 'request': request
             }
             return render(request, template_name, context, status_code=HTTPStatus.BAD_REQUEST.value)

        try:
            db_session.add(new_obj)
            for field_name, data in fields_to_process_later.items():
                 relation_type = data['type']
                 value = data['value']
                 attr = data['attr']

                 if relation_type in ('manytoone', 'onetoone'):
                      fk_column_name = field_name
                      try:
                          if value == '' and attr.local_remote_pairs[0][0].nullable:
                              setattr(new_obj, fk_column_name, None)
                              
                          elif value != '':
                              setattr(new_obj, fk_column_name, int(value))
                      except ValueError:
                          logger.warning(f"Generic Add View for {model_name}: Invalid integer value '{value}' for FK field '{fk_column_name}' during post-add processing.")

                 elif relation_type == 'manytomany':
                      related_model = attr.mapper.class_
                      related_obj_ids_to_link = value 
                      if related_obj_ids_to_link:
                           try:
                               related_objects_to_link = db_session.query(related_model).filter(
                                   getattr(related_model, 'id').in_(related_obj_ids_to_link)
                               ).all()
                               getattr(new_obj, field_name).extend(related_objects_to_link)
                               
                           except Exception as link_e:
                                logger.error(f"Generic Add View for {model_name}: Error linking objects for manytomany relationship '{field_name}': {link_e}", exc_info=True)
                                request.add_context('form_errors', {field_name: f'Error linking related {related_model.__name__} objects.'})

            form_errors = request.get_context('form_errors', {})
            if form_errors:
                 logger.warning(f"Generic Add View for {model_name}: Form errors detected after relationship processing. Not attempting to commit.")
                 db_session.rollback()
                 mapper = inspect(model)
                 form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, new_obj)

                 context = {
                     'model_name': model_name,
                     'is_add': True,
                     'form_fields_data': form_fields_data,
                     'relationship_fields_data': relationship_fields_data,
                     'object': new_obj,
                     'form_errors': form_errors,
                     'error_message': "Please correct the errors below.",
                     'admin_base_template': 'admin/base.html',
                     'router': router,
                     'config': config,
                     'request': request
                 }
                 return render(request, template_name, context, status_code=HTTPStatus.BAD_REQUEST.value)

            db_session.commit()

            logger.info(f"Generic Add View for {model_name}: Successfully saved new object with ID {getattr(new_obj, 'id', 'N/A')}.")

            list_url = f"/admin/{model_name.lower()}/"
            response = redirect(list_url)
            return response

        except IntegrityError as e:
             db_session.rollback()
             logger.error(f"Generic Add View for {model_name}: Database integrity error saving object: {e}", exc_info=True)
             form_errors = {'_general': 'Database integrity error. This might be due to duplicate unique values.'}
             request.add_context('form_errors', form_errors)
             request.add_context('error_message', "Database error: Could not save object.")
             mapper = inspect(model)
             form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, new_obj)

             context = {
                 'model_name': model_name,
                 'is_add': True,
                 'form_fields_data': form_fields_data,
                 'relationship_fields_data': relationship_fields_data,
                 'object': new_obj,
                 'form_errors': form_errors,
                 'error_message': "Database error: Could not save object. Please check your input.",
                 'admin_base_template': 'admin/base.html',
                 'router': router,
                 'config': config,
                 'request': request
             }
             return render(request, template_name, context, status_code=HTTPStatus.CONFLICT.value)

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Generic Add View for {model_name}: Error saving new object: {e}.")
            request.add_context('error_message', f"An unexpected error occurred: {e}")
            mapper = inspect(model)
            form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, new_obj)

            context = {
                'model_name': model_name,
                'is_add': True,
                'form_fields_data': form_fields_data,
                'relationship_fields_data': relationship_fields_data,
                'object': new_obj,
                'error_message': f"An unexpected error occurred: {e}",
                'admin_base_template': 'admin/base.html',
                'router': router,
                'config': config,
                'request': request
            }
            return return_500(request, exception=e)

    else:
        logger.info(f"Generic Add View for {model_name}: Displaying add form.")
        try:
            mapper = inspect(model)
            form_fields_data, relationship_fields_data, file_upload_fields = get_model_form_data(db_session, mapper, None)

            context: Dict[str, Any] = {
                "model_name": model_name,
                "is_add": True,
                "object": None,
                "form_fields_data": form_fields_data,
                "relationship_fields_data": relationship_fields_data,
                'admin_base_template': 'admin/base.html',
                'router': router,
                'config': config,
                'request': request
            }

            return render(request, template_name, context)

        except Exception as e:
            logger.exception(f"Generic Add View for {model_name}: Error rendering add form: {e}")
            return return_500(request, exception=e)


@PermissionRequired(lambda request: f"change_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "change_unknown_model")
def generic_change_view(request: Request, model: Type[BaseModel], object_id: Any) -> Response:
    """
    Handles the generic "change" view for editing existing instances of a database model.

    This view supports both displaying a pre-filled form for editing (GET request)
    and processing form submissions to update an existing object in the database (POST request).
    It dynamically handles various SQLAlchemy column types and relationships (Many-to-One,
    One-to-One, Many-to-Many) based on the provided model's schema.

    It includes:
    - Dynamic permission checking using the `@PermissionRequired` decorator.
    - Retrieval of the existing object by `object_id`.
    - Handling of file uploads, including replacing old files and validating new ones.
    - Type conversion for different database column types (String, Integer, Boolean, DateTime, JSON).
    - Management of Many-to-Many relationships by clearing and re-adding associated objects.
    - Robust error handling for object not found, form validation, and database integrity issues.
    - Redirection upon successful update or re-rendering the form with errors.

    :param request: The incoming request object, containing parsed body, files,
                    database session, configuration, and router information.
    :type request: Request
    :param model: The SQLAlchemy `BaseModel` class whose instance is to be changed.
    :type model: Type[BaseModel]
    :param object_id: The primary key or unique identifier of the object to be changed.
    :type object_id: Any
    :returns: A `Response` object, either a redirect on success, or a rendered form
              (potentially with errors) on failure or for initial display.
    :rtype: Response
    """
    model_name = getattr(model, '__name__', 'UnknownModel')
    logger.info(f"Handling generic change view for model: {model_name}, ID: {object_id}, Method: {request.method} for {request.path}.")

    db_session: Optional[SQLASession] = request.db_session
    config: Optional[Config] = request.config
    router: Any = request.router

    if not hasattr(request, '_context') or request._context is None:
        request._context = {}

    if 'form_errors' not in request._context:
        request._context['form_errors'] = {}

    if not all([db_session, config, router]):
        logger.critical(f"Generic Change View for {model_name}, ID {object_id}: Missing required dependencies on request (db_session, config, router).")
        return return_500(request, message="Internal Server Error: Missing dependencies.")

    obj = db_session.query(model).get(object_id)

    if obj is None:
        logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Object not found.")
        return return_404(request, message=f"{model_name} with ID {object_id} not found.")

    template_name = f'admin/generic_form.html'

    if request.method == HTTPMethod.POST:
        logger.info(f"Generic Change View for {model_name}, ID {object_id}: Processing POST request.")

        form_data: Dict[str, Any] = request.parsed_body if hasattr(request, 'parsed_body') and request.parsed_body is not None else {}
        uploaded_files: Dict[str, Union[UploadedFile, List[UploadedFile]]] = request.files if hasattr(request, 'files') and request.files is not None else {}
        mapper = inspect(model)
        all_model_attributes = {attr.key: attr for attr in mapper.attrs}
        fields_to_process_later: Dict[str, Any] = {}
        for field_name, attr in all_model_attributes.items():
             excluded_fields = ['id', 'created_at', 'updated_at', 'published_at', 'password', 'is_superuser', 'role_id', 'csrfmiddlewaretoken', 'slug']
             if field_name in excluded_fields:
                 continue
             if hasattr(attr, 'columns') and attr.columns:
                  column = attr.columns[0]
                  is_file_field = isinstance(column.type, (String, Text)) and (field_name.endswith('_file') or field_name.endswith('_path'))
                  if is_file_field:
                       if field_name in uploaded_files:
                            uploaded_file_object: Union[UploadedFile, List[UploadedFile]] = uploaded_files[field_name]
                            if isinstance(uploaded_file_object, list):
                                if uploaded_file_object:
                                    uploaded_file_object = uploaded_file_object[0]
                                    logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Multiple files uploaded for '{field_name}'. Processing only the first one.")
                                else:
                                    uploaded_file_object = None
                            if isinstance(uploaded_file_object, UploadedFile):
                                allowed_types = getattr(config, 'UPLOAD_ALLOWED_TYPES', None)
                                max_size_mb = getattr(config, 'UPLOAD_MAX_SIZE_MB', None)
                                saved_file_path = save_uploaded_file(uploaded_file_object, config, model_name,
                                                                    allowed_types=allowed_types, max_size_mb=max_size_mb)
                                if saved_file_path:
                                    old_file_path = getattr(obj, field_name, None)
                                    if old_file_path and isinstance(old_file_path, str):
                                        logger.debug(f"Generic Change View for {model_name}, ID {object_id}: Old file found for '{field_name}': {old_file_path}. Attempting to delete.")
                                        delete_saved_file(old_file_path, config)

                                    setattr(obj, field_name, saved_file_path)
                                    logger.info(f"Generic Change View for {model_name}, ID {object_id}: Assigned new saved file path '{saved_file_path}' to field '{field_name}'.")
                                else:
                                    validation_error_msg = validate_uploaded_file(uploaded_file_object, allowed_types, max_size_mb)
                                    if validation_error_msg:
                                        request.context['form_errors'][field_name] = validation_error_msg
                                        logger.warning(f"Generic Change View for {model_name}, ID {object_id}: File validation failed for '{field_name}': {validation_error_msg}")
                                    else:
                                        request.context['form_errors'][field_name] = 'Failed to upload file.'
                                        logger.error(f"Generic Change View for {model_name}, ID {object_id}: Failed to save uploaded file for '{field_name}' without specific validation error.")

                            elif uploaded_file_object is not None:
                                 logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Unexpected type for uploaded file '{field_name}': {type(uploaded_file_object)}. Skipping file processing.")
                                 request.context['form_errors'][field_name] = 'Invalid file format received.'
                       else:
                            logger.debug(f"Generic Change View for {model_name}, ID {object_id}: No file uploaded for field '{field_name}'. Keeping existing value.")
                  else:
                       if field_name in form_data:
                            value = form_data[field_name]

                            if isinstance(column.type, (String, Text)):
                                setattr(obj, field_name, value)
                                logger.debug(f"Generic Change View for {model_name}, ID {object_id}: Set string/text field '{field_name}' to '{value}'.")

                            elif isinstance(column.type, Integer):
                                 try:
                                     if value == '' and column.nullable:
                                         setattr(obj, field_name, None)
                                     else:
                                         setattr(obj, field_name, int(value))
                                         
                                 except ValueError:
                                     logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Invalid integer value '{value}' for field '{field_name}'.")
                                     request.add_context('form_errors', {field_name: 'Invalid integer value.'})
                                     setattr(obj, field_name, None if column.nullable else 0)

                            elif isinstance(column.type, Boolean):
                                 setattr(obj, field_name, value == 'on')
                                 
                            elif isinstance(column.type, DateTime):
                                 try:
                                     if value == '' and column.nullable:
                                         setattr(obj, field_name, None)
                                         
                                     else:
                                         setattr(obj, field_name, datetime.fromisoformat(value) if value else None)
                                         
                                 except ValueError:
                                     logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Invalid datetime value '{value}' for field '{field_name}'.")
                                     request.add_context('form_errors', {field_name: 'Invalid datetime value.'})
                                     setattr(obj, field_name, None if column.nullable else datetime.utcnow())

                            elif isinstance(column.type, JSON):
                                 try:
                                     if value == '' and column.nullable:
                                         setattr(obj, field_name, None)
                                         
                                     else:
                                         setattr(obj, field_name, json.loads(value))
                                         
                                 except json.JSONDecodeError:
                                     logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Invalid JSON value for field '{field_name}'.")
                                     request.add_context('form_errors', {field_name: 'Invalid JSON value.'})
                                     setattr(obj, field_name, None if column.nullable else {})
                                 except TypeError:
                                     logger.warning(f"Generic Change View for {model_name}, ID {object_id}: JSON value for field '{field_name}' is not a string. Keeping existing value.")

                            else:
                                 setattr(obj, field_name, value)
                        
                       else:
                            if hasattr(attr, 'columns') and attr.columns and isinstance(attr.columns[0].type, Boolean):
                                 setattr(obj, field_name, False)

             elif isinstance(attr, RelationshipProperty):
                 relation_type = attr.direction.name.lower()

                 if relation_type in ('manytoone', 'onetoone'):
                     if attr.local_remote_pairs:
                         form_field_name_for_post = attr.local_remote_pairs[0][0].name
                         value = form_data.get(form_field_name_for_post)
                         if value is not None and value != '':
                              try:
                                  value = int(value)
                              except ValueError:
                                  logger.warning(f"Generic Change View: Invalid ID '{value}' for {form_field_name_for_post} (manytoone/onetoone).")
                                  value = None
                         elif value == '':
                              value = None
                         
                         fields_to_process_later[form_field_name_for_post] = {'type': relation_type, 'value': value, 'attr': attr}
 
                 elif relation_type == 'manytomany':
                    form_field_name = field_name
                    received_values = request.parsed_body.getlist(f"{form_field_name}[]")
                    if not received_values:
                        received_values = request.parsed_body.getlist(form_field_name)

                    cleaned_ids = []
                    for item in received_values:
                        if item is not None and str(item).strip() != '':
                            try:
                                cleaned_ids.append(int(item))
                            except ValueError:
                                logger.warning(f"Generic Change View: Invalid permission ID format: {item}. Skipping.")
                    
                    fields_to_process_later[form_field_name] = {'type': relation_type, 'value': cleaned_ids, 'attr': attr}

             elif field_name in form_data:
                 value = form_data.get(field_name)
                 setattr(obj, field_name, value)

        form_errors = request.get_context('form_errors', {})
        if form_errors:
             logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Form errors detected before commit. Not attempting to commit.")
             db_session.rollback()
             mapper = inspect(model)
             form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, obj)

             context = {
                 'model_name': model_name,
                 'object': obj,
                 'is_add': False,
                 'form_fields_data': form_fields_data,
                 'relationship_fields_data': relationship_fields_data,
                 'form_errors': form_errors,
                 'error_message': "Please correct the errors below.",
                 'admin_base_template': 'admin/base.html',
                 'router': router,
                 'config': config,
                 'request': request
             }
             return render(request, template_name, context, status_code=HTTPStatus.BAD_REQUEST.value)


        try:
            for field_name, data in fields_to_process_later.items():
                 relation_type = data['type']
                 value = data['value']
                 attr = data['attr']
                 if relation_type in ('manytoone', 'onetoone'):
                      fk_column_name = field_name
                      try:
                          if value == '' and attr.local_remote_pairs[0][0].nullable:
                              setattr(obj, fk_column_name, None)
                              
                          elif value != '':
                              setattr(obj, fk_column_name, int(value))
                              
                      except ValueError:
                          logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Invalid integer value '{value}' for FK field '{fk_column_name}' during pre-commit processing.")

                 elif relation_type == 'manytomany':
                      related_model = attr.mapper.class_
                      related_obj_ids_to_link = value

                      getattr(obj, field_name).clear()
                      if related_obj_ids_to_link:
                           try:
                               related_objects_to_link = db_session.query(related_model).filter(
                                   getattr(related_model, 'id').in_(related_obj_ids_to_link)
                               ).all()

                               getattr(obj, field_name).extend(related_objects_to_link)

                           except Exception as link_e:
                                logger.error(f"Generic Change View for {model_name}, ID {object_id}: Error linking objects for manytomany relationship '{field_name}': {link_e}", exc_info=True)
                                request.add_context('form_errors', {field_name: f'Error linking related {related_model.__name__} objects.'})

            form_errors = request.get_context('form_errors', {})
            if form_errors:
                 logger.warning(f"Generic Change View for {model_name}, ID {object_id}: Form errors detected after relationship processing. Not attempting to commit.")
                 db_session.rollback()
                 mapper = inspect(model)
                 form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, obj)

                 context = {
                     'model_name': model_name,
                     'object': obj,
                     'is_add': False,
                     'form_fields_data': form_fields_data,
                     'relationship_fields_data': relationship_fields_data,
                     'form_errors': form_errors,
                     'error_message': "Please correct the errors below.",
                     'admin_base_template': 'admin/base.html',
                     'router': router,
                     'config': config,
                     'request': request
                 }
                 return render(request, template_name, context, status_code=HTTPStatus.BAD_REQUEST.value)

            db_session.commit()

            logger.info(f"Generic Change View for {model_name}, ID {object_id}: Successfully updated object.")

            list_url = f"/admin/{model_name.lower()}/"
            response = redirect(list_url)
            
            return response

        except IntegrityError as e:
             db_session.rollback()
             logger.error(f"Generic Change View for {model_name}, ID {object_id}: Database integrity error updating object: {e}", exc_info=True)
             form_errors = {'_general': 'Database integrity error. This might be due to duplicate unique values.'}
             request.add_context('form_errors', form_errors)
             request.add_context('error_message', "Database error: Could not update object.")
             mapper = inspect(model)
             form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, obj)

             context = {
                 'model_name': model_name,
                 'object': obj,
                 'is_add': False,
                 'form_fields_data': form_fields_data,
                 'relationship_fields_data': relationship_fields_data,
                 'form_errors': form_errors,
                 'error_message': "Database error: Could not update object. Please check your input.",
                 'admin_base_template': 'admin/base.html',
                 'router': router,
                 'config': config,
                 'request': request
             }
             return render(request, template_name, context, status_code=HTTPStatus.CONFLICT.value)

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Generic Change View for {model_name}, ID {object_id}: Error updating object: {e}.")
            request.add_context('error_message', f"An unexpected error occurred: {e}")
            mapper = inspect(model)
            form_fields_data, relationship_fields_data, _ = get_model_form_data(db_session, mapper, obj)

            context = {
                'model_name': model_name,
                'object': obj,
                'is_add': False,
                'form_fields_data': form_fields_data,
                'relationship_fields_data': relationship_fields_data,
                'error_message': f"An unexpected error occurred: {e}",
                'admin_base_template': 'admin/base.html',
                'router': router,
                'config': config,
                'request': request
            }
            return return_500(request, exception=e)


    else:
        logger.info(f"Generic Change View for {model_name}, ID {object_id}: Displaying change form.")
        try:
            mapper = inspect(model)
            form_fields_data, relationship_fields_data, file_upload_fields = get_model_form_data(db_session, mapper, obj)

            context: Dict[str, Any] = {
                "model_name": model_name,
                "object": obj,
                "is_add": False,
                "form_fields_data": form_fields_data,
                "relationship_fields_data": relationship_fields_data,
                'admin_base_template': 'admin/base.html',
                'router': router,
                'config': config,
                'request': request
            }

            return render(request, template_name, context)

        except Exception as e:
            logger.exception(f"Generic Change View for {model_name}, ID {object_id}: Error rendering change form: {e}")
            return return_500(request, exception=e)

@PermissionRequired(lambda request: f"view_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "view_unknown_model")
def generic_list_view(request: Request, model: Type[BaseModel]) -> Response:
    """
    Handles the generic "list" view for displaying, searching, filtering, and paginating
    instances of a database model.

    This view dynamically generates a list of objects based on the provided model's schema
    and query parameters. It supports various SQLAlchemy column types and relationships
    for advanced filtering and sorting capabilities.

    It includes:
    - Dynamic permission checking using the `@PermissionRequired` decorator, ensuring users
      can only view models they are authorized to access.
    - Retrieval and pagination of model instances from the database.
    - Full-text search functionality across string-based columns.
    - Advanced filtering options:
        - Range filtering for date/datetime and numeric fields (e.g., `created_at_min`, `price_max`).
        - Null/Not Null checks for any field, including relationship foreign keys (e.g., `author_id_isnull=true`).
        - Exact match filtering for boolean, integer, float, and string fields.
        - Filtering based on Many-to-One relationships (e.g., selecting objects linked to a specific related entity).
        - Filtering based on Many-to-Many relationships (e.g., finding objects associated with a particular related entity).
        - Filtering for the existence/non-existence of One-to-One related objects.
    - Customizable sorting by any sortable model column, in ascending or descending order.
    - Dynamic determination of fields to display in the list, excluding sensitive or overly large fields by default.
    - Generation of metadata for filter controls to be used in the UI, including available choices for
      relationship-based filters.
    - Robust error handling for database session issues or unexpected exceptions during processing.
    - Rendering of an HTML template (`admin/generic_list.html`) with the prepared data.

    :param request: The incoming request object, containing query parameters,
                    path parameters, database session, and other request-specific data.
    :type request: Request
    :param model: The SQLAlchemy `BaseModel` class whose instances are to be listed.
    :type model: Type[BaseModel]
    :returns: A `Response` object, typically a rendered HTML page displaying the list
              of objects, or an error response if issues occur (e.g., database session missing).
    :rtype: Response
    """
    model_name = getattr(model, '__name__', 'UnknownModel')
    logger.info(f"Rendering generic list view for model: {model_name} for {request.method} {request.path}.")

    db_session: Optional[SQLASession] = request.db_session

    if not db_session:
        logger.critical(f"Database session is not available in generic_list_view for model {model_name}.")
        return return_500(request, message="Internal Server Error: Database session missing.")

    try:
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))
        page = max(1, page)
        per_page = max(1, per_page)
        search_query = request.query_params.get('q', '').strip()
        
        filter_params = {
            key: value for key, value in request.query_params.items()
            if key not in ['page', 'per_page', 'q', 'sort_by', 'sort_order']
        }
        
        sort_by = request.query_params.get('sort_by', 'id')
        sort_order = request.query_params.get('sort_order', 'asc').lower()
        if sort_order not in ['asc', 'desc']:
            logger.warning(f"Invalid sort_order '{sort_order}' received. Defaulting to 'asc'.")
            sort_order = 'asc'

        base_query: Query = db_session.query(model)

        if search_query:
            mapper = inspect(model)
            searchable_fields = [
                column.name for column in model.__table__.columns
                if isinstance(column.type, (String, Text))
            ]

            if searchable_fields:
                search_conditions = []
                for field_name in searchable_fields:
                    if hasattr(model, field_name):
                         search_conditions.append(
                             getattr(model, field_name).ilike(f"%{search_query}%")
                         )
                    else:
                         logger.warning(f"Searchable field '{field_name}' not found as an attribute on model {model_name}. Skipping search condition for this field.")

                if search_conditions:
                    base_query = base_query.filter(or_(*search_conditions))
                    
                else:
                     logger.warning(f"No valid searchable fields found for model {model_name} after checking attributes.")
            else:
                logger.warning(f"No searchable fields found for model {model_name}. Search query '{search_query}' will be ignored.")

        if filter_params:
            mapper = inspect(model)
            filter_conditions = []
            filterable_attributes = {attr.key: attr for attr in mapper.attrs if hasattr(attr, 'columns') or isinstance(attr, RelationshipProperty)}
            processed_filter_keys = set()

            for param_key, param_value in filter_params.items():
                if param_key in processed_filter_keys or param_value == '':
                    continue

                if param_key.endswith('_min'):
                    field_name = param_key[:-4]
                    max_param_key = f"{field_name}_max"
                    processed_filter_keys.add(param_key)
                    processed_filter_keys.add(max_param_key)

                    attr = filterable_attributes.get(field_name)
                    if attr and hasattr(attr, 'columns') and attr.columns:
                         column = attr.columns[0]
                         min_value_str = param_value.strip()
                         max_value_str = filter_params.get(max_param_key, '').strip()

                         if isinstance(column.type, (DateTime, Date)):
                              min_date = None
                              max_date = None
                              try:
                                  if min_value_str:
                                       min_date = datetime.fromisoformat(min_value_str) if isinstance(column.type, DateTime) else date.fromisoformat(min_value_str)
                                       filter_conditions.append(column >= min_date)
                                       
                              except ValueError:
                                  logger.warning(f"Invalid date/datetime min value '{min_value_str}' for field '{field_name}'.")

                              try:
                                  if max_value_str:
                                       max_date = datetime.fromisoformat(max_value_str) if isinstance(column.type, DateTime) else date.fromisoformat(max_value_str)
                                       if isinstance(column.type, DateTime) and isinstance(max_date, date):
                                           max_date = datetime.combine(max_date, datetime.max.time())

                                       filter_conditions.append(column <= max_date)
                                       
                              except ValueError:
                                  logger.warning(f"Invalid date/datetime max value '{max_value_str}' for field '{field_name}'.")

                         elif isinstance(column.type, (Integer, Float, Numeric)):
                              min_num = None
                              max_num = None
                              try:
                                  if min_value_str:
                                       min_num = float(min_value_str) if isinstance(column.type, (Float, Numeric)) else int(min_value_str)
                                       filter_conditions.append(column >= min_num)
                                       
                              except ValueError:
                                  logger.warning(f"Invalid numeric min value '{min_value_str}' for field '{field_name}'.")

                              try:
                                  if max_value_str:
                                       max_num = float(max_value_str) if isinstance(column.type, (Float, Numeric)) else int(max_value_str)
                                       filter_conditions.append(column <= max_num)
                                       
                              except ValueError:
                                  logger.warning(f"Invalid numeric max value '{max_value_str}' for field '{field_name}'.")
                         else:
                            logger.warning(f"Range filter requested for non-numeric/non-date field '{field_name}' ({type(column.type).__name__}). Skipping.")

                elif param_key.endswith('_isnull'):
                    field_name = param_key[:-8]
                    processed_filter_keys.add(param_key)
                    attr = filterable_attributes.get(field_name)
                    if attr:
                         if hasattr(attr, 'columns') and attr.columns:
                              column_or_relation = attr.columns[0]
                         elif isinstance(attr, RelationshipProperty):
                              column_or_relation = attr

                         if column_or_relation:
                              if param_value.lower() == 'true':
                                  if hasattr(column_or_relation, 'is_'):
                                       filter_conditions.append(column_or_relation.is_(null()))
                                       logger.debug(f"Applied isnull filter: {field_name} IS NULL")

                                  elif isinstance(column_or_relation, RelationshipProperty):
                                       if column_or_relation.direction.name in ('MANYTOONE', 'ONETOONE'):
                                            if column_or_relation.local_remote_pairs:
                                                 fk_column = column_or_relation.local_remote_pairs[0][0]
                                                 filter_conditions.append(fk_column.is_(null()))
                                                 logger.debug(f"Applied isnull filter for relationship {field_name}: FK IS NULL")
                                            else:
                                                 logger.warning(f"Could not determine FK for relationship '{field_name}' for isnull filter.")
                                       elif column_or_relation.direction.name == 'MANYTOMANY':
                                            filter_conditions.append(~column_or_relation.any())
                                            logger.debug(f"Applied isnull filter for Many-to-Many relationship {field_name}: ~any()")
                                       else:
                                            logger.warning(f"Unsupported relationship direction '{column_or_relation.direction.name}' for isnull filter on '{field_name}'.")

                              elif param_value.lower() == 'false':
                                  if hasattr(column_or_relation, 'isnot'):
                                       filter_conditions.append(column_or_relation.isnot(null()))
                                       logger.debug(f"Applied isnotnull filter: {field_name} IS NOT NULL")

                                  elif isinstance(column_or_relation, RelationshipProperty):
                                       if column_or_relation.direction.name in ('MANYTOONE', 'ONETOONE'):
                                            if column_or_relation.local_remote_pairs:
                                                 fk_column = column_or_relation.local_remote_pairs[0][0]
                                                 filter_conditions.append(fk_column.isnot(null()))
                                                 logger.debug(f"Applied isnotnull filter for relationship {field_name}: FK IS NOT NULL")
                                            else:
                                                 logger.warning(f"Could not determine FK for relationship '{field_name}' for isnotnull filter.")
                                       elif column_or_relation.direction.name == 'MANYTOMANY':
                                            filter_conditions.append(column_or_relation.any())
                                            logger.debug(f"Applied isnotnull filter for Many-to-Many relationship {field_name}: any()")
                                       else:
                                            logger.warning(f"Unsupported relationship direction '{column_or_relation.direction.name}' for isnotnull filter on '{field_name}'.")
                              else:
                                  logger.warning(f"Invalid isnull filter value '{param_value}' for field '{field_name}'. Expected 'true' or 'false'.")
                         else:
                              logger.warning(f"Nullable filter requested for attribute '{field_name}' which is not a column or Relationship. Skipping.")

                elif param_key not in processed_filter_keys:
                    attr = filterable_attributes.get(param_key)
                    if isinstance(attr, RelationshipProperty):
                         if attr.direction.name == 'MANYTOONE':
                             if attr.local_remote_pairs:
                                 fk_column = attr.local_remote_pairs[0][0]
                                 try:
                                     fk_value = int(param_value)
                                     filter_conditions.append(fk_column == fk_value)
                                     
                                 except ValueError:
                                     logger.warning(f"Invalid integer value '{param_value}' for Many-to-One filter field '{param_key}' (FK column: {fk_column.name}).")
                             else:
                                 logger.warning(f"Could not determine FK column for Many-to-One relationship '{param_key}'. Skipping filter.")

                         elif attr.direction.name == 'MANYTOMANY':
                             related_model = attr.mapper.class_
                             try:
                                 related_obj_id = int(param_value)
                                 filter_conditions.append(attr.any(related_model.id == related_obj_id))
                                 
                             except ValueError:
                                 logger.warning(f"Invalid integer value '{param_value}' for Many-to-Many filter field '{param_key}'. Expected related object ID.")
                             except Exception as manytomany_filter_e:
                                 logger.error(f"Error applying Many-to-Many filter for '{param_key}': {manytomany_filter_e}", exc_info=True)

                    elif hasattr(attr, 'columns') and attr.columns:
                        column = attr.columns[0]
                        if isinstance(column.type, Boolean):
                            if param_value.lower() in ['true', 'false']:
                                boolean_value = param_value.lower() == 'true'
                                filter_conditions.append(column == boolean_value)
                                
                            else:
                                logger.warning(f"Invalid boolean filter value '{param_value}' for field '{param_key}'.")

                        elif isinstance(column.type, Integer):
                            try:
                                int_value = int(param_value)
                                filter_conditions.append(column == int_value)
                                
                            except ValueError:
                                logger.warning(f"Invalid integer filter value '{param_value}' for field '{param_key}'.")

                        elif isinstance(column.type, (Float, Numeric)):
                            try:
                                float_value = float(param_value)
                                filter_conditions.append(column == float_value)
                                
                            except ValueError:
                                logger.warning(f"Invalid numeric filter value '{param_value}' for field '{param_key}'.")

                        elif isinstance(column.type, (String, Text)):
                             filter_conditions.append(column == param_value)  

                    else:
                        logger.warning(f"Filter parameter '{param_key}' does not correspond to a filterable model attribute on {model_name}. Skipping filter.")

            if filter_conditions:
                base_query = base_query.filter(and_(*filter_conditions))

        mapper = inspect(model)
        sortable_attributes = {attr.key: attr for attr in mapper.attrs if hasattr(attr, 'columns') and attr.columns}

        if sort_by in sortable_attributes:
             sort_column = sortable_attributes[sort_by].columns[0]
             if sort_order == 'asc':
                  base_query = base_query.order_by(asc(sort_column))
                  
             else:
                  base_query = base_query.order_by(desc(sort_column))
                  
        else:
             logger.warning(f"Invalid or non-sortable field '{sort_by}' for sorting. Defaulting to sorting by 'id' ASC.")
             if hasattr(model, 'id'):
                 base_query = base_query.order_by(asc(model.id))
                 sort_by = 'id'
                 sort_order = 'asc'
             else:
                 logger.warning(f"Model {model_name} does not have an 'id' column. No default sorting applied.")
                 sort_by = None
                 sort_order = None

        pagination_data = paginate_query(base_query, page=page, per_page=per_page)
        paginated_objects = pagination_data['objects']
        mapper = inspect(model)
        all_columns = model.__table__.columns
        excluded_fields_from_list = ['id', 'created_at', 'updated_at', 'slug', 'password', 'is_superuser', 'role_id']
        excluded_fields_from_list.extend([c.name for c in all_columns if isinstance(c.type, (String, Text)) and (c.name.endswith('_path') or c.name.endswith('_file'))])
        excluded_fields_from_list = list(set(excluded_fields_from_list))
        fields_to_display_data: List[Dict[str, Any]] = []
        sortable_columns = [c.name for c in all_columns if c.name not in excluded_fields_from_list and not isinstance(c.type, JSON)]

        for column in all_columns:
             if column.name not in excluded_fields_from_list:
                  field_data: Dict[str, Any] = {'name': column.name}
                  if isinstance(column.type, DateTime):
                       field_data['type'] = 'datetime'
                  elif isinstance(column.type, Date):
                       field_data['type'] = 'date'
                  elif isinstance(column.type, Boolean):
                       field_data['type'] = 'boolean'
                  elif isinstance(column.type, Integer):
                       field_data['type'] = 'integer'
                  elif isinstance(column.type, String):
                       field_data['type'] = 'string'
                  elif isinstance(column.type, Text):
                       field_data['type'] = 'text'
                  elif isinstance(column.type, JSON):
                       field_data['type'] = 'json'
                  elif isinstance(column.type, (Float, Numeric)):
                       field_data['type'] = 'numeric'
                  else:
                       field_data['type'] = 'other'

                  field_data['sortable'] = field_data['name'] in sortable_columns
                  field_data['is_current_sort'] = field_data['name'] == sort_by
                  fields_to_display_data.append(field_data)

        fields_to_display_data = sorted(fields_to_display_data, key=lambda x: x['name'])
        filterable_fields_data: Dict[str, Dict[str, Any]] = {}
        mapper = inspect(model)

        for attr in mapper.attrs:
             field_name = attr.key
             if hasattr(attr, 'columns') and attr.columns:
                  column = attr.columns[0]
                  column_type = column.type
                  column_name = column.name
                  is_nullable = column.nullable
                  if isinstance(column_type, Boolean):
                       filterable_fields_data[column_name] = {
                           'name': column_name,
                           'label': column_name.replace('_', ' ').capitalize(),
                           'type': 'boolean',
                           'control': 'select',
                           'choices': [
                               {'value': '', 'text': f'-- All {column_name.replace("_", " ").capitalize()} --'},
                               {'value': 'True', 'text': 'Yes'},
                               {'value': 'False', 'text': 'No'},
                           ],
                           'current_value': filter_params.get(column_name, '')
                       }

                  elif isinstance(column_type, (DateTime, Date)):
                       filterable_fields_data[column_name] = {
                           'name': column_name,
                           'label': column_name.replace('_', ' ').capitalize(),
                           'type': 'date_range',
                           'control': 'date_range_inputs',
                           'current_min_value': filter_params.get(f'{column_name}_min', ''),
                           'current_max_value': filter_params.get(f'{column_name}_max', ''),
                       }

                  elif isinstance(column_type, (Integer, Float, Numeric)):
                       filterable_fields_data[column_name] = {
                           'name': column_name,
                           'label': column_name.replace('_', ' ').capitalize(),
                           'type': 'numeric_range',
                           'control': 'numeric_range_inputs',
                           'current_min_value': filter_params.get(f'{column_name}_min', ''),
                           'current_max_value': filter_params.get(f'{column_name}_max', ''),
                       }
                       
                  if is_nullable and not isinstance(column_type, Boolean):
                       nullable_param_name = f'{column_name}_isnull'
                       filterable_fields_data[nullable_param_name] = {
                           'name': nullable_param_name,
                           'label': f'{column_name.replace("_", " ").capitalize()} (Is Null)',
                           'type': 'nullable',
                           'control': 'select',
                           'choices': [
                               {'value': '', 'text': '-- All --'},
                               {'value': 'true', 'text': 'Is Null'},
                               {'value': 'false', 'text': 'Is Not Null'},
                           ],
                           'current_value': filter_params.get(nullable_param_name, '')
                       }

             elif isinstance(attr, RelationshipProperty):
                  if attr.direction.name == 'MANYTOONE':
                       fk_column_name = None
                       is_nullable_fk = False
                       if attr.local_remote_pairs:
                            fk_column = attr.local_remote_pairs[0][0]
                            fk_column_name = fk_column.name
                            is_nullable_fk = fk_column.nullable 
                       if fk_column_name:
                            related_model = attr.mapper.class_
                            try:
                                related_objects = db_session.query(related_model).order_by(getattr(related_model, 'id')).all()
                                filter_choices = [{'value': str(getattr(obj, 'id', '')), 'text': str(obj)} for obj in related_objects]
                                filter_choices.insert(0, {'value': '', 'text': f'-- All {related_model.__name__} --'})

                                filterable_fields_data[fk_column_name] = {
                                    'name': fk_column_name,
                                    'label': attr.key.replace('_', ' ').capitalize(),
                                    'type': 'manytoone',
                                    'control': 'select',
                                    'choices': filter_choices,
                                    'current_value': filter_params.get(fk_column_name, '')
                                }
                                
                                if is_nullable_fk:
                                     nullable_param_name = f'{fk_column_name}_isnull'
                                     filterable_fields_data[nullable_param_name] = {
                                         'name': nullable_param_name,
                                         'label': f'{attr.key.replace("_", " ").capitalize()} (Is Null)',
                                         'type': 'nullable',
                                         'control': 'select',
                                         'choices': [
                                             {'value': '', 'text': '-- All --'},
                                             {'value': 'true', 'text': 'Is Null'},
                                             {'value': 'false', 'text': 'Is Not Null'},
                                         ],
                                         'current_value': filter_params.get(nullable_param_name, '')
                                     }
                                     
                            except Exception as related_query_e:
                                 logger.error(f"Error querying related objects for filtering '{field_name}' on model {model_name}: {related_query_e}", exc_info=True)

                  elif attr.direction.name == 'MANYTOMANY':
                       related_model = attr.mapper.class_
                       relation_param_base = attr.key

                       try:
                           related_objects = db_session.query(related_model).order_by(getattr(related_model, 'id')).all()
                           filter_choices = [{'value': str(getattr(obj, 'id', '')), 'text': str(obj)} for obj in related_objects]
                           filter_choices.insert(0, {'value': '', 'text': f'-- All {related_model.__name__} --'})
                           specific_related_param_name = relation_param_base
                           filterable_fields_data[specific_related_param_name] = {
                               'name': specific_related_param_name,
                               'label': attr.key.replace('_', ' ').capitalize(),
                               'type': 'manytomany_specific',
                               'control': 'select',
                               'choices': filter_choices,
                               'current_value': filter_params.get(specific_related_param_name, '')
                           }
                           
                           nullable_param_name = f'{relation_param_base}_isnull'
                           filterable_fields_data[nullable_param_name] = {
                               'name': nullable_param_name,
                               'label': f'{attr.key.replace("_", " ").capitalize()} (Is Null)',
                               'type': 'nullable',
                               'control': 'select',
                               'choices': [
                                   {'value': '', 'text': '-- All --'},
                                   {'value': 'true', 'text': 'Is Null (Has None)'},
                                   {'value': 'false', 'text': 'Is Not Null (Has Any)'},
                               ],
                               'current_value': filter_params.get(nullable_param_name, '')
                           }

                       except Exception as related_query_e:
                            logger.error(f"Error querying related objects for Many-to-Many filtering '{field_name}' on model {model_name}: {related_query_e}", exc_info=True)

                  elif attr.direction.name == 'ONETOONE':
                       relation_param_base = attr.key

                       nullable_param_name = f'{relation_param_base}_isnull'
                       filterable_fields_data[nullable_param_name] = {
                           'name': nullable_param_name,
                           'label': f'{attr.key.replace("_", " ").capitalize()} (Is Null)',
                           'type': 'nullable',
                           'control': 'select',
                           'choices': [
                               {'value': '', 'text': '-- All --'},
                               {'value': 'true', 'text': 'Is Null (Does Not Exist)'},
                               {'value': 'false', 'text': 'Is Not Null (Exists)'},
                           ],
                           'current_value': filter_params.get(nullable_param_name, '')
                       }
                       

        filterable_fields_data = dict(sorted(filterable_fields_data.items(), key=lambda item: item[1]['label']))

        context: Dict[str, Any] = {
            "model_name": model_name,
            "objects": paginated_objects,
            "fields_to_display": fields_to_display_data,
            "pagination": pagination_data,
            "search_query": search_query,
            "filter_params": filter_params,
            "filterable_fields_data": filterable_fields_data,
            "current_sort_by": sort_by,
            "current_sort_order": sort_order,
        }
        return render(request, "admin/generic_list.html", context)

    except Exception as e:
        logger.exception(f"Error rendering generic list view for model {model_name} for {request.method} {request.path}.")
        return return_500(request, exception=e)

@PermissionRequired(lambda request: f"view_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "view_unknown_model")
def generic_detail_view(request: Request, model: Type[BaseModel], object_id: Any) -> Response:
    """
    Handles the generic "detail" view for displaying the attributes of a single
    instance of a database model.

    This view retrieves a specific object by its ID and dynamically prepares its fields
    for display. It handles various SQLAlchemy column types and relationships,
    formatting them appropriately for presentation in a detail page.

    It includes:
    - Dynamic permission checking using the `@PermissionRequired` decorator to ensure
      the user is authorized to view the specific model's details.
    - Retrieval of the existing object by `object_id` from the database.
    - Handling of "object not found" scenarios by returning a 404 response.
    - Exclusion of sensitive or internal fields (e.g., 'id', 'password') from display.
    - Special formatting for different data types:
        - SQLAlchemy Relationships (ManyToOne, OneToOne): Displays string representation.
        - SQLAlchemy Relationships (ManyToMany): Displays a list of string representations.
        - File/Path Fields (ending with `_file` or `_path`): Constructs a full URL for download/display
          based on `UPLOAD_URL` from `request.config`.
        - JSON Fields: Pretty-prints the JSON content.
        - Boolean Fields: Displays "Yes" or "No".
        - DateTime Fields: Formats as "YYYY-MM-DD HH:MM:SS".
        - Other standard column types are displayed as is.
    - Sorting of displayed fields alphabetically by name for consistent presentation.
    - Robust error handling for missing database session/configuration or other runtime exceptions,
      returning a 500 response.
    - Rendering of an HTML template (`admin/generic_detail.html`) with the object's details.

    :param request: The incoming request object, containing path parameters,
                    database session, application configuration, etc.
    :type request: Request
    :param model: The SQLAlchemy `BaseModel` class whose instance details are to be viewed.
    :type model: Type[BaseModel]
    :param object_id: The primary key or unique identifier of the object to be displayed.
    :type object_id: Any
    :returns: A `Response` object, typically a rendered HTML page showing the object's
              details, or an HTTP 404/500 error response if the object is not found
              or an internal error occurs.
    :rtype: Response
    """
    model_name = getattr(model, '__name__', 'UnknownModel')
    logger.info(f"Rendering generic detail view for model: {model_name}, ID: {object_id} for {request.method} {request.path}.")

    db_session: Optional[SQLASession] = request.db_session
    config: Optional[Config] = request.config

    if not db_session or not config:
        logger.critical(f"Database session or Config is not available in generic_detail_view for model {model_name}, ID {object_id}.")
        return return_500(request, message="Internal Server Error: Database session or Config missing.")

    try:
        obj = db_session.query(model).get(object_id)
        
        if obj is None:
            logger.warning(f"Object with ID {object_id} not found for model {model_name} in detail view for {request.method} {request.path}.")
            return return_404(request, message=f"{model_name} with ID {object_id} not found.")


        mapper = inspect(model)
        fields_to_display_data: List[Dict[str, Any]] = []

        upload_url_base = getattr(config, 'UPLOAD_URL', '/uploads/')

        for attr in mapper.attrs:
             field_name = attr.key
             excluded_fields = ['id', 'password', 'is_superuser', 'role_id', 'csrfmiddlewaretoken', 'slug']

             if field_name in excluded_fields:
                 continue

             field_value = getattr(obj, field_name, None)
             field_type = 'other'
             display_value: Any = field_value

             if isinstance(attr, RelationshipProperty):
                  relation_type = attr.direction.name.lower()
                  field_type = relation_type 

                  if relation_type in ('manytoone', 'onetoone'):
                       display_value = str(field_value) if field_value else "None"

                  elif relation_type == 'manytomany':
                       if field_value:
                            if isinstance(field_value, (list, tuple)):
                                display_value = [str(related_obj) for related_obj in field_value]
                            else:
                                logger.warning(f"Generic Detail View for {model_name}, ID {object_id}: Unexpected type for manytomany relationship '{field_name}': {type(field_value)}. Displaying raw value.")
                                display_value = str(field_value) if field_value else "None"
                       else:
                            display_value = []

             elif hasattr(attr, 'columns') and attr.columns:
                  column = attr.columns[0]
                  column_name = column.name

                  if isinstance(column.type, (String, Text)) and (column_name.endswith('_file') or column_name.endswith('_path')):
                       field_type = 'file_upload'
                       if field_value and isinstance(field_value, str):
                            file_url = urljoin(upload_url_base, field_value)
                            display_value = {'url': file_url, 'path': field_value, 'filename': os.path.basename(field_value or '')}
                       else:
                            display_value = None

                  elif isinstance(column.type, JSON):
                       field_type = 'json'
                       try:
                           display_value = json.dumps(field_value, indent=2) if field_value is not None else "None"
                       except TypeError:
                           logger.warning(f"Generic Detail View for {model_name}, ID {object_id}: Could not serialize JSON field '{field_name}' to string. Displaying raw value.")
                           display_value = str(field_value) if field_value is not None else "None"

                  elif isinstance(column.type, Boolean):
                       field_type = 'boolean'
                       display_value = "Yes" if field_value else "No"
                  elif isinstance(column.type, DateTime):
                       field_type = 'datetime'
                       display_value = field_value.strftime('%Y-%m-%d %H:%M:%S') if isinstance(field_value, datetime) else "None"
                  elif isinstance(column.type, Integer):
                       field_type = 'integer'
                  elif isinstance(column.type, String):
                       field_type = 'string'
                  elif isinstance(column.type, Text):
                       field_type = 'text'
                  else:
                       field_type = 'other'

             fields_to_display_data.append({
                 'name': field_name,
                 'value': display_value,
                 'type': field_type,
             })

        fields_to_display_data = sorted(fields_to_display_data, key=lambda x: x['name'])


        context: Dict[str, Any] = {
            "model_name": model_name,
            "object": obj,
            "fields_to_display": fields_to_display_data,
        }

        return render(request, "admin/generic_detail.html", context)

    except Exception as e:
        logger.exception(f"Error retrieving or rendering object {object_id} for model {model_name} in detail view for {request.method} {request.path}.")
        return return_500(request, exception=e)

@PermissionRequired(lambda request: f"delete_{request.path_params.get('model_name').lower()}" if request.path_params and request.path_params.get('model_name') else "delete_unknown_model")
def generic_delete_view(request: Request, model: Type[BaseModel], object_id: Any) -> Response:
    
    """
    Handles the generic "delete" view for removing instances of a database model.

    This view is specifically designed to process POST requests for deletion to prevent
    accidental deletions via GET requests. It performs the following actions:
    - **Permission Checking**: Uses the `@PermissionRequired` decorator to ensure the user
      has the necessary permission (`delete_<model_name>`).
    - **Dependency Check**: Verifies the presence of a database session and configuration.
    - **HTTP Method Enforcement**: Ensures the request method is POST.
    - **Object Retrieval**: Fetches the object to be deleted by its `object_id`.
    - **AdminUser Specific Protections**: Implements special logic to prevent:
        - Deletion of the primary superuser (ID 1).
        - Non-primary superusers from deleting other superusers.
        - Non-superusers from deleting any `AdminUser`.
    - **Associated File Deletion**: Iterates through model attributes to identify and delete
      any associated files (e.g., fields ending with '_file' or '_path') from the filesystem
      before deleting the database record.
    - **Database Deletion**: Deletes the object from the database and commits the transaction.
    - **Redirection**: Redirects to the model's list view upon successful deletion.
    - **Error Handling**: Provides robust error handling for object not found, forbidden
      operations, and unexpected exceptions during the deletion process.

    :param request: The incoming request object, containing the database session,
                    configuration, and the current user.
    :type request: Request
    :param model: The SQLAlchemy `BaseModel` class whose instance is to be deleted.
    :type model: Type[BaseModel]
    :param object_id: The primary key or unique identifier of the object to be deleted.
    :type object_id: Any
    :returns: A `Response` object, typically a redirect on success, or an error response
              (404, 403, or 500) on failure.
    :rtype: Response
    """
    model_name = getattr(model, '__name__', 'UnknownModel')
    logger.info(f"Handling generic delete view for model: {model_name}, ID: {object_id}, Method: {request.method} for {request.path}.")
    db_session: Optional[SQLASession] = request.db_session
    config: Optional[Config] = request.config
    current_user: Optional[Any] = getattr(request, 'user', None)

    if not db_session or not config:
        logger.critical(f"Database session or Config is not available in generic_delete_view for model {model_name}, ID {object_id}.")
        return return_500(request, message="Internal Server Error: Database session or Config missing.")

    if request.method != HTTPMethod.POST:
        logger.warning(f"Received non-POST request for delete submission for model {model_name}, ID {object_id}: {request.method}")
        return Response(body=b"Method Not Allowed", status_code=HTTPStatus.METHOD_NOT_ALLOWED.value, headers={'Content-Type': 'text/plain', 'Allow': HTTPMethod.POST.value})

    try:
        obj = db_session.query(model).get(object_id)
        if obj is None:
            logger.warning(f"Object with ID {object_id} not found for model {model_name} in delete view for {request.method} {request.path}.")
            return return_404(request, message=f"{model_name} with ID {object_id} not found for deletion.")

        if isinstance(obj, AdminUser):
            if obj.id == 1:
                logger.warning(f"AdminUser with ID 1 (superuser) cannot be deleted. Attempt by user ID: {current_user.id if current_user else 'N/A'}.")
                return Response(status_code=HTTPStatus.FORBIDDEN.value,
                                data=b"Deletion Forbidden: The primary superuser cannot be deleted.",
                                headers={'Content-Type': 'text/plain'})

            if current_user and isinstance(current_user, AdminUser) and hasattr(current_user, 'is_superuser'):
                if obj.is_superuser:
                    if current_user.id != 1:
                        logger.warning(f"AdminUser '{current_user.username}' (ID: {current_user.id}) attempted to delete superuser AdminUser '{obj.username}' (ID: {obj.id}). Only AdminUser ID 1 can delete other superusers.")
                        return Response(status_code=HTTPStatus.FORBIDDEN.value,
                                        data=b"Deletion Forbidden: Only primary superuser (ID 1) can delete other superusers.",
                                        headers={'Content-Type': 'text/plain'})
                    else:
                        logger.info(f"AdminUser ID 1 is attempting to delete superuser AdminUser '{obj.username}' (ID: {obj.id}). Proceeding.")

                else:
                    if not current_user.is_superuser and current_user.id != 1:
                        logger.warning(f"AdminUser '{current_user.username}' (ID: {current_user.id}) attempted to delete non-superuser AdminUser '{obj.username}' (ID: {obj.id}). Only superusers or Admin ID 1 can delete other admins.")
                        return Response(status_code=HTTPStatus.FORBIDDEN.value,
                                        data=b"Deletion Forbidden: You do not have sufficient privileges to delete other administrators.",
                                        headers={'Content-Type': 'text/plain'})
                    else:
                        logger.info(f"AdminUser '{current_user.username}' (ID: {current_user.id}) is attempting to delete non-superuser AdminUser '{obj.username}' (ID: {obj.id}). Proceeding.")
            else:
                logger.warning(f"Unauthorized or invalid user attempting to delete an AdminUser. Current user: {current_user}.")
                return Response(status_code=HTTPStatus.FORBIDDEN.value,
                                data=b"Deletion Forbidden: You must be an authenticated AdminUser with sufficient privileges.",
                                headers={'Content-Type': 'text/plain'})

        mapper = inspect(model)
        for attr in mapper.attrs:
             if hasattr(attr, 'columns') and attr.columns:
                 column = attr.columns[0]
                 if isinstance(column.type, (String, Text)) and (attr.key.endswith('_file') or attr.key.endswith('_path')):
                        file_path = getattr(obj, attr.key, None)
                        if file_path and isinstance(file_path, str):
                            
                            delete_saved_file(file_path, config)
                        elif file_path:
                            logger.warning(f"Generic Delete View for {model_name}, ID {object_id}: Associated file path for field '{attr.key}' is not a string: {file_path}. Skipping deletion.")

        db_session.delete(obj)
        db_session.commit()
        logger.info(f"Successfully deleted object with ID {object_id} for model {model_name}.")
        list_url = f"/admin/{model_name.lower()}/"
        return redirect(list_url)

    except Exception as e:
        db_session.rollback()
        logger.exception(f"Error deleting object with ID {object_id} for model {model_name} for {request.method} {request.path}.")
        return return_500(request, exception=e)