import logging
import json
from typing import Dict, Any, Optional, List
from http import HTTPStatus
from datetime import datetime
import math

from sqlalchemy.orm import Session as SQLASession, RelationshipProperty, Query
from sqlalchemy.types import JSON, String, Integer, DateTime, Boolean, Text

from lback.core.types import Request
from lback.core.response import HTMLResponse, Response, JSONResponse, RedirectResponse
from lback.core.templates import TemplateRenderer, TemplateNotFound
from lback.core.error_handler import ErrorHandler
from lback.admin.registry import admin
from lback.utils.static_files import static



logger = logging.getLogger(__name__)


def render(request: Request, template_name: str, context: Optional[Dict[str, Any]] = None, status_code: int = HTTPStatus.OK.value) -> Response:
    """
    Renders a template and returns an HTMLResponse.

    This is a shortcut function to simplify view functions.
    It retrieves the template renderer from the request context
    and uses it to render the specified template with the given context.
    Also injects common request-related context data into the template.

    Args:
        request: The incoming Request object.
        template_name: The name of the template file (e.g., "admin/login.html").
        context: An optional dictionary of context data to pass to the template.
        status_code: The HTTP status code for the response (default is 200 OK).

    Returns:
        An HTMLResponse object containing the rendered template content.

    Raises:
        TemplateNotFound: If the specified template does not exist.
        Exception: For any other errors during rendering.
    """
    if context is None:
        context = {}
    renderer: Optional[TemplateRenderer] = request.template_renderer
    context.setdefault('registered_models', list(admin.get_registered_models().keys()))

    config = getattr(request, 'config', None) 

    if config is None:
        logger.error("Config object not found in request. Cannot add static function to context.")
        raise Exception("Application configuration is not available.")
    if not renderer:
        logger.error("TemplateRenderer not available on request for render shortcut.")
        return return_500(request, message="Template renderer not available.")

    try:
        full_context_for_rendering = context.copy()
        full_context_for_rendering['request'] = request
        full_context_for_rendering['current_user'] = request.user
        full_context_for_rendering['session'] = request.session
        full_context_for_rendering['config'] = request.config
        full_context_for_rendering['csrf_token'] = request.get_context('csrf_token')
        full_context_for_rendering['router'] = request.router
        full_context_for_rendering['getattr'] = getattr
        full_context_for_rendering['static'] = lambda path: static(config, path)



        rendered_html = renderer.render_to_string(template_name, **full_context_for_rendering)
        return HTMLResponse(content=rendered_html, status_code=status_code)

    except TemplateNotFound:
        logger.error(f"Template '{template_name}' not found during render shortcut for {request.method} {request.path}.")
        error_handler: Optional[ErrorHandler] = request.error_handler
        if error_handler:
             return error_handler.handle_404(request)
        else:
             return Response(body=f"Template '{template_name}' not found.".encode('utf-8'), status_code=HTTPStatus.NOT_FOUND.value, headers={'Content-Type': 'text/plain'})

    except Exception as e:
        logger.exception(f"Error rendering template '{template_name}' for {request.method} {request.path} using render shortcut.")
        error_handler: Optional[ErrorHandler] = request.error_handler
        if error_handler:
             return error_handler.handle_exception(e, request)
        else:
             return Response(body=b"Internal Server Error: Template rendering failed.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})


def redirect(to_url: str, status_code: int = HTTPStatus.FOUND.value) -> RedirectResponse:
    """
    Returns a RedirectResponse.

    Args:
        to_url: The URL to redirect to.
        status_code: The HTTP status code for the redirect (default is 302 Found).
                     Common redirect codes: 301 Moved Permanently, 302 Found, 303 See Other, 307 Temporary Redirect, 308 Permanent Redirect.

    Returns:
        A RedirectResponse object.
    """
    if status_code not in (301, 302, 303, 307, 308):
         logger.warning(f"Using non-standard redirect status code: {status_code}")

    logger.debug(f"Redirecting to: {to_url} with status {status_code}")
    return RedirectResponse(to_url, status_code=status_code)


def json_response(data: Any, status_code: int = HTTPStatus.OK.value) -> JSONResponse:
    """
    Returns a JSONResponse.

    Args:
        data: The Python data structure to be serialized to JSON.
        status_code: The HTTP status code for the response (default is 200 OK).

    Returns:
        A JSONResponse object.
    """
    logger.debug(f"Returning JSON response with status {status_code}.")
    return JSONResponse(content=data, status_code=status_code)

def return_404(request: Request, message: str = "Not Found") -> Response:
    """
    Returns a 404 Not Found response using the configured error handler if available.
    Otherwise, returns a basic 404 text response.

    Args:
        request: The incoming Request object.
        message: An optional message (may or may not be used by the error handler).

    Returns:
        A Response object representing a 404 Not Found error.
    """
    logger.debug(f"Returning 404 response for {request.method} {request.path} via shortcut.")
    error_handler: Optional[ErrorHandler] = request.error_handler

    if error_handler:
        return error_handler.handle_404(request)
    else:
        logger.critical("Error handler not available on request to return 404. Returning basic 404 response.")
        return Response(body=message.encode('utf-8'), status_code=HTTPStatus.NOT_FOUND.value, headers={'Content-Type': 'text/plain'})

def return_403(request: Request, message: str = "Forbidden") -> Response:
    """
    Returns a 403 Forbidden response using the configured error handler if available.
    Otherwise, returns a basic 403 text response.

    Args:
        request: The incoming Request object.
        message: An optional message (may or may not be used by the error handler).

    Returns:
        A Response object representing a 403 Forbidden error.
    """
    logger.warning(f"Returning 403 response for {request.method} {request.path} via shortcut. Message: {message}")
    error_handler: Optional[ErrorHandler] = request.error_handler

    if error_handler:
        return error_handler.handle_403(request, message=message) 
    else:
        logger.critical("Error handler not available on request to return 403. Returning basic 403 response.")
        return Response(body=message.encode('utf-8'), status_code=HTTPStatus.FORBIDDEN.value, headers={'Content-Type': 'text/plain'})


def return_500(request: Request, message: str = "Internal Server Error", exception: Optional[Exception] = None) -> Response:
    """
    Returns a 500 Internal Server Error response using the configured error handler if available.
    Otherwise, returns a basic 500 text response.

    Args:
        request: The incoming Request object.
        message: An optional message (may or may not be used by the error handler).
        exception: An optional exception that caused the error, for logging/debugging purposes by the error handler.

    Returns:
        A Response object representing a 500 Internal Server Error.
    """
    logger.error(f"Returning 500 response for {request.method} {request.path} via shortcut.", exc_info=exception)
    error_handler: Optional[ErrorHandler] = request.error_handler

    if error_handler:
        return error_handler.handle_exception(exception or RuntimeError(message), request)
    else:
        logger.critical("Error handler not available on request to return 500. Returning basic 500 response.")
        response_body = b"Internal Server Error: An unexpected error occurred."
        return Response(body=response_body, status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value, headers={'Content-Type': 'text/plain'})


def get_model_form_data(db_session: SQLASession, mapper: Any, obj: Optional[Any] = None) -> tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], List[str]]:
    """
    Inspects a SQLAlchemy model's mapper to determine form fields,
    relationship fields with choices, and file upload fields.
    Includes support for Many-to-One, One-to-One, and Many-to-Many relationships.
    Optionally takes an object to populate current values for change forms.
    Returns a tuple: (form_fields_data, relationship_fields_data, file_upload_fields).
    """
    form_fields_data: List[Dict[str, Any]] = []
    relationship_fields_data: Dict[str, Dict[str, Any]] = {}
    file_upload_fields: List[str] = []

    for attr in mapper.attrs:
        field_name = attr.key

        excluded_fields = ['id', 'created_at', 'updated_at', 'published_at', 'password', 'is_superuser', 'role_id', 'csrfmiddlewaretoken', 'slug']
        if field_name in excluded_fields:
            continue

        if isinstance(attr, RelationshipProperty):
            logger.debug(f"_get_model_form_data: Identified Relationship field: {field_name} with direction {attr.direction.name}")
            related_model = attr.mapper.class_ 
            relation_type = attr.direction.name.lower() 
            try:
                related_objects = db_session.query(related_model).all()
                logger.debug(f"_get_model_form_data: Fetched {len(related_objects)} related objects for '{field_name}' ({related_model.__name__}).")
                choices = []
                for related_obj in related_objects:
                     choice_id = getattr(related_obj, 'id', None)
                     choices.append({
                         'id': choice_id,
                         'text': str(related_obj),
                     })
                if relation_type in ('manytoone', 'onetoone'):
                    fk_column_name = None
                    current_related_obj_id = None
                    if attr.local_remote_pairs:
                        fk_column = attr.local_remote_pairs[0][0]
                        fk_column_name = fk_column.name
                        logger.debug(f"_get_model_form_data: Identified Foreign Key column name for '{field_name}': {fk_column_name}")
                        if obj is not None:
                             current_related_obj_id = getattr(obj, fk_column_name, None)
                             logger.debug(f"_get_model_form_data: Current related object ID for '{field_name}' ({fk_column_name}): {current_related_obj_id}")
                        for choice in choices:
                             choice['selected'] = (choice['id'] == current_related_obj_id)
                    if fk_column_name:
                         relationship_fields_data[fk_column_name] = {
                             'field_name': fk_column_name,
                             'relation_name': field_name,
                             'type': relation_type,
                             'related_model_name': related_model.__name__,
                             'choices': choices,
                             'nullable': fk_column.nullable 
                         }
                         form_fields_data.append({'name': fk_column_name, 'type': relation_type, 'nullable': fk_column.nullable})
                         logger.debug(f"_get_model_form_data: Added {relation_type} field data for {fk_column_name}.")

                    else:
                         logger.warning(f"_get_model_form_data: Could not determine Foreign Key column name for {relation_type} relationship '{field_name}' on model {mapper.class_.__name__}. Skipping.")

                elif relation_type == 'manytomany':
                    logger.debug(f"_get_model_form_data: Identified Many-to-Many relationship field: {field_name}")
                    current_related_obj_ids: List[Any] = []
                    if obj is not None:
                         currently_linked_objects = getattr(obj, field_name, [])
                         current_related_obj_ids = [getattr(linked_obj, 'id', None) for linked_obj in currently_linked_objects if getattr(linked_obj, 'id', None) is not None]
                         logger.debug(f"_get_model_form_data: Current related object IDs for '{field_name}': {current_related_obj_ids}")
                    for choice in choices:
                         choice['selected'] = (choice['id'] in current_related_obj_ids)
                    relationship_fields_data[field_name] = {
                        'field_name': field_name,
                        'type': relation_type,
                        'related_model_name': related_model.__name__,
                        'choices': choices,
                        'nullable': True 
                    }
                    form_fields_data.append({'name': field_name, 'type': relation_type, 'nullable': True})
                    logger.debug(f"_get_model_form_data: Added manytomany field data for {field_name}.")

            except Exception as related_query_e:
                logger.error(f"_get_model_form_data: Error querying related objects for {relation_type} relationship '{field_name}' on model {mapper.class_.__name__}: {related_query_e}", exc_info=True)
        elif hasattr(attr, 'columns') and attr.columns:
            column = attr.columns[0]
            column_name = column.name
            column_value = getattr(obj, column_name) if obj is not None else None

            if isinstance(column.type, (String, Text)) and (column_name.endswith('_file') or column_name.endswith('_path')):
                logger.debug(f"_get_model_form_data: Identified file upload field: {column_name}")
                file_upload_fields.append(column_name)
                form_fields_data.append({'name': column_name, 'type': 'file_upload', 'current_value': column_value, 'nullable': column.nullable})

            elif isinstance(column.type, JSON):
                 logger.debug(f"_get_model_form_data: Identified JSON field: {column_name}")
                 json_value_str = json.dumps(column_value, indent=2) if column_value is not None else ""
                 form_fields_data.append({'name': column_name, 'type': 'json', 'current_value': json_value_str, 'nullable': column.nullable})
                 
            elif isinstance(column.type, Boolean):
                 logger.debug(f"_get_model_form_data: Identified Boolean field: {column_name}")
                 form_fields_data.append({'name': column_name, 'type': 'boolean', 'current_value': column_value, 'nullable': column.nullable})

            elif isinstance(column.type, DateTime):
                 logger.debug(f"_get_model_form_data: Identified DateTime field: {column_name}")
                 datetime_value_str = column_value.strftime('%Y-%m-%dT%H:%M') if isinstance(column_value, datetime) else ""
                 form_fields_data.append({'name': column_name, 'type': 'datetime', 'current_value': datetime_value_str, 'nullable': column.nullable})

            elif isinstance(column.type, Integer):
                 is_fk_for_many_to_one = any(
                     isinstance(rel, RelationshipProperty) and
                     rel.direction.name == 'MANYTOONE' and
                     any(pair[0].name == column_name for pair in rel.local_remote_pairs)
                     for rel in mapper.relationships
                 )
                 if not is_fk_for_many_to_one:
                      logger.debug(f"_get_model_form_data: Identified Integer field: {column_name}")
                      form_fields_data.append({'name': column_name, 'type': 'integer', 'current_value': column_value, 'nullable': column.nullable})
                 else:
                      logger.debug(f"_get_model_form_data: Skipping Integer field {column_name} as it's a foreign key for a Many-to-One relationship.")
            elif isinstance(column.type, String):
                 if column.type.length:
                      logger.debug(f"_get_model_form_data: Identified String field (CharField-like): {column_name}")
                      form_fields_data.append({'name': column_name, 'type': 'string', 'length': column.type.length, 'current_value': column_value, 'nullable': column.nullable})
                 else: 
                      logger.debug(f"_get_model_form_data: Identified String field (TextField-like): {column_name}")
                      form_fields_data.append({'name': column_name, 'type': 'text', 'current_value': column_value, 'nullable': column.nullable})
            else:
                 logger.debug(f"_get_model_form_data: Identified other field type ({type(column.type).__name__}): {column_name}")
                 form_fields_data.append({'name': column_name, 'type': 'other', 'sqlalchemy_type': type(column.type).__name__, 'current_value': column_value, 'nullable': column.nullable})
    form_fields_data = sorted(form_fields_data, key=lambda x: x['name'])
    return form_fields_data, relationship_fields_data, file_upload_fields


def paginate_query(query: Query, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Paginates a SQLAlchemy query.

    Args:
        query: The SQLAlchemy query object.
        page: The current page number (1-based index).
        per_page: The number of items per page.

    Returns:
        A dictionary containing pagination data:
        - objects: List of objects for the current page.
        - total_objects: Total number of objects across all pages.
        - total_pages: Total number of pages.
        - current_page: The current page number.
        - per_page: Items per page.
        - has_prev: Boolean, whether there is a previous page.
        - has_next: Boolean, whether there is a next page.
        - prev_num: Previous page number (None if no previous page).
        - next_num: Next page number (None if no next page).
        - iter_pages: Generator for page numbers to display in pagination control.
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    total_objects = query.count()
    total_pages = math.ceil(total_objects / per_page) if total_objects > 0 else 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page
    paginated_objects = query.limit(per_page).offset(offset).all()

    has_prev = page > 1
    has_next = page < total_pages
    prev_num = page - 1 if has_prev else None
    next_num = page + 1 if has_next else None

    def iter_pages(left_edge=2, left_current=2, right_current=2, right_edge=2):
        last = 0
        for num in range(1, total_pages + 1):
            if num <= left_edge or \
               (page - left_current <= num <= page + right_current) or \
               num > total_pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    return {
        'objects': paginated_objects,
        'total_objects': total_objects,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': per_page,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': prev_num,
        'next_num': next_num,
        'iter_pages': iter_pages()
    }