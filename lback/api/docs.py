import json
import logging
from http import  HTTPStatus
from typing import Any, Dict, Type
from sqlalchemy.orm import RelationshipProperty

from lback.core.router import Router, Route
from lback.core.router import Router, Route
from lback.core.signals import dispatcher
from lback.core.types import TypeConverter

from .serializer import BaseModelSerializer

logger = logging.getLogger(__name__)


class APIDocs:
    """
    Generates OpenAPI (Swagger) documentation for the Lback API.
    Aims to automatically collect documentation details from registered routes and views.
    Integrates SignalDispatcher to emit events during the documentation generation process.
    """
    def __init__(self, router: Router, title: str = "Lback API", version: str = "1.0.0", description: str = "API Documentation"):
        """
        Intializes the APIDocs generator.
        Emits 'api_docs_initialized' signal.

        Args:
            router: The framework's central Router instance.
            title: The title of the API documentation.
            version: The version of the API.
            description: A description of the API.
        """
        if not isinstance(router, Router):
             logger.error("APIDocs initialized without a valid Router instance.")
        self.router = router
        self.title = title
        self.version = version
        self.description = description
        self.paths: Dict[str, Any] = {}
        self.components: Dict[str, Any] = {
            "schemas": {},
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
        logger.info("APIDocs initialized.")

        dispatcher.send("api_docs_initialized", sender=self, title=self.title, version=self.version, description=self.description)
        logger.debug("Signal 'api_docs_initialized' sent.")


    def collect_documentation(self):
        """
        Collects documentation details from the registered routes and views.
        This method orchestrates the automatic documentation generation.
        Emits 'api_docs_collection_started' and 'api_docs_collection_finished' signals.
        """
        logger.info("Collecting API documentation from routes and views.")

        dispatcher.send("api_docs_collection_started", sender=self)
        logger.debug("Signal 'api_docs_collection_started' sent.")

        self.paths = {}
        processed_routes_count = 0
        skipped_routes_count = 0

        for route in self.router.routes:
            if self._document_route(route):
                processed_routes_count += 1
            else:
                skipped_routes_count += 1


        logger.info(f"Documentation collection completed. Found {len(self.paths)} paths. Processed {processed_routes_count} routes, Skipped {skipped_routes_count}.")
        dispatcher.send("api_docs_collection_finished", sender=self, paths_count=len(self.paths), processed_routes=processed_routes_count, skipped_routes=skipped_routes_count)
        logger.debug("Signal 'api_docs_collection_finished' sent.")


    def _document_route(self, route: Route) -> bool:
        """
        Documents a single route by inspecting its view and methods.
        Emits 'api_docs_route_documented' signal on success.
        Emits 'api_docs_route_skipped' signal if a route cannot be documented.

        Args:
            route: The Route object to document.

        Returns:
            True if the route was successfully documented (at least one method), False otherwise.
        """
        path = route.path
        view_class = route.view

        if not hasattr(view_class, 'methods') or not isinstance(view_class.methods, list) or not view_class.methods:
             logger.warning(f"View {getattr(view_class, '__name__', 'N/A')} for path '{path}' has no defined or empty 'methods' attribute. Skipping documentation.")
             dispatcher.send("api_docs_route_skipped", sender=self, route=route, reason="no_methods")
             logger.debug(f"Signal 'api_docs_route_skipped' (no_methods) sent for path '{path}'.")
             return False

        if path not in self.paths:
            self.paths[path] = {}

        documented_methods_count = 0

        for method in view_class.methods:
            method_lower = method.lower()
            handler_method = getattr(view_class, method_lower, None)

            if handler_method and callable(handler_method):
                operation_spec: Dict[str, Any] = {}
                docstring = handler_method.__doc__
                if docstring:
                    lines = docstring.strip().split('\n')
                    operation_spec["summary"] = lines[0].strip()
                    if len(lines) > 1:
                         operation_spec["description"] = "\n".join(lines[1:]).strip()
                    logger.debug(f"Extracted summary/description for {method} {path}.")

                if route._variable_names:
                    operation_spec["parameters"] = []
                    for param_name, param_type_converter in route._variable_names.items():
                        param_type = "string"
                        if hasattr(param_type_converter, '__name__'):
                            converter_name = param_type_converter.__name__
                            if 'int' in converter_name.lower():
                                param_type = "integer"
                            elif 'float' in converter_name.lower():
                                param_type = "number"
                            elif 'bool' in converter_name.lower():
                                param_type = "boolean"

                        param_spec = {
                             "name": param_name,
                             "in": "path",
                             "required": True,
                             "schema": {"type": param_type},

                         }
                        operation_spec["parameters"].append(param_spec)
                    logger.debug(f"Documented path parameters for {method} {path}.")
                else:
                    operation_spec.setdefault("parameters", [])

                response_spec = {
                    str(getattr(view_class, 'default_response_status', 200)): {
                        "description": "Successful Response"

                    },
                }
                operation_spec["responses"] = response_spec
                logger.debug(f"Documented responses for {method} {path}. (Basic)")

                if route.requires_auth:
                     operation_spec["security"] = [{"bearerAuth": []}]

                self.paths[path][method_lower] = operation_spec
                logger.debug(f"Documented {method} {path}.")
                documented_methods_count += 1
            else:
                 logger.warning(f"View {getattr(view_class, '__name__', 'N/A')} for path '{path}' lists method '{method}' but no callable handler method '{method_lower}' is defined. Skipping documentation for this method.")

        if documented_methods_count > 0:
            dispatcher.send("api_docs_route_documented", sender=self, route=route, path=path, documented_methods_count=documented_methods_count)
            logger.debug(f"Signal 'api_docs_route_documented' sent for path '{path}'. Documented methods: {documented_methods_count}.")
            return True
        else:
            dispatcher.send("api_docs_route_skipped", sender=self, route=route, reason="no_callable_methods")
            logger.debug(f"Signal 'api_docs_route_skipped' (no_callable_methods) sent for path '{path}'.")
            return False


    def generate_openapi(self) -> Dict[str, Any]:
        """
        Generates the full OpenAPI specification dictionary.
        Emits 'openapi_spec_generated' signal.
        """
        if not self.paths:
             logger.warning("No paths collected. Running documentation collection.")
             self.collect_documentation()

        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "paths": self.paths,
            "components": self.components,
        }
        logger.info("OpenAPI specification generated.")
        dispatcher.send("openapi_spec_generated", sender=self, spec=openapi_spec)
        logger.debug("Signal 'openapi_spec_generated' sent.")

        return openapi_spec

    def as_json(self) -> str:
        """Returns the OpenAPI specification as a JSON string."""
        return json.dumps(self.generate_openapi(), ensure_ascii=False, indent=2)


    def register_serializer_schema(self, serializer_class: Type[BaseModelSerializer], schema_name: str):
        """
        Generates an OpenAPI schema from a Serializer and adds it to components.
        Emits 'api_docs_serializer_schema_registered' signal.
        Note: This is a basic placeholder implementation. A real implementation would
        inspect the serializer fields to build the schema.
        """
        logger.debug(f"Registering schema for serializer: {serializer_class.__name__} as {schema_name}.")
        dispatcher.send("api_docs_serializer_schema_registered", sender=self, serializer_class=serializer_class, schema_name=schema_name)
        logger.debug(f"Signal 'api_docs_serializer_schema_registered' sent for serializer '{serializer_class.__name__}'.")

        schema = {
            "type": "object",
            "properties": {
            },
            "required": []
        }
        self.components["schemas"][schema_name] = schema
        logger.info(f"Schema '{schema_name}' registered from serializer '{serializer_class.__name__}'.")


    def _document_route(self, route: Route) -> bool:
        """
        Documents a single route by inspecting its view and methods.
        Emits 'api_docs_route_documented' signal on success.
        Emits 'api_docs_route_skipped' signal if a route cannot be documented.

        Args:
            route: The Route object to document.

        Returns:
            True if the route was successfully documented (at least one method), False otherwise.
        """
        path = route.path
        view_class = route.view_class

        if not hasattr(view_class, 'methods') or not isinstance(view_class.methods, list) or not view_class.methods:
             logger.warning(f"View {getattr(view_class, '__name__', 'N/A')} for path '{path}' has no defined or empty 'methods' attribute. Skipping documentation.")
             dispatcher.send("api_docs_route_skipped", sender=self, route=route, reason="no_methods")
             logger.debug(f"Signal 'api_docs_route_skipped' (no_methods) sent for path '{path}'.")
             return False

        if path not in self.paths:
            openapi_path = self._convert_path_to_openapi(path, route._variable_names)
            self.paths[openapi_path] = {}

        documented_methods_count = 0

        for method in view_class.methods:
            method_lower = method.lower()
            handler_method = getattr(view_class, method_lower, None)

            if handler_method and callable(handler_method):
                operation_spec: Dict[str, Any] = {}
                docstring = handler_method.__doc__
                if docstring:
                    lines = docstring.strip().split('\n')
                    operation_spec["summary"] = lines[0].strip()
                    if len(lines) > 1:
                        operation_spec["description"] = "\n".join(lines[1:]).strip()
                    logger.debug(f"Extracted summary/description for {method} {path}.")

                if route._variable_names:
                    operation_spec["parameters"] = []
                    for param_name, param_type_converter in route._variable_names.items():
                        param_type = "string"
                        if isinstance(param_type_converter, TypeConverter):
                            param_type = param_type_converter.openapi_type
                        elif hasattr(param_type_converter, '__name__'):
                            converter_name = param_type_converter.__name__.lower()
                            if 'int' in converter_name: param_type = "integer"
                            elif 'float' in converter_name: param_type = "number"
                            elif 'bool' in converter_name: param_type = "boolean"

                        param_spec = {
                            "name": param_name,
                            "in": "path",
                            "required": True,
                            "schema": {"type": param_type},
                        }
                        operation_spec["parameters"].append(param_spec)
                    logger.debug(f"Documented path parameters for {method} {path}.")
                else:
                    operation_spec.setdefault("parameters", [])

                if method_lower in ["post", "put", "patch"]:
                    if hasattr(view_class, 'serializer_class') and view_class.serializer_class is not None:
                        schema_name = view_class.serializer_class.__name__
                        self.register_serializer_schema(view_class.serializer_class, schema_name)
                        operation_spec["requestBody"] = {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                                }
                            }
                        }
                        logger.debug(f"Documented request body for {method} {path} using {schema_name}.")
                    else:
                        logger.warning(f"View {getattr(view_class, '__name__', 'N/A')} for path '{path}' method '{method}' has no serializer_class for request body.")
                        operation_spec["requestBody"] = {"content": {"application/json": {"schema": {"type": "object"}}}} 

                response_spec = {
                    str(getattr(view_class, 'default_response_status', 200)): {
                        "description": "Successful Response"
                    },
                    str(HTTPStatus.BAD_REQUEST.value): {
                        "description": "Bad Request / Validation Error",
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}, "errors": {"type": "object"}}}}}
                    },
                    str(HTTPStatus.NOT_FOUND.value): {
                        "description": "Not Found",
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}
                    },
                    str(HTTPStatus.UNAUTHORIZED.value): {
                        "description": "Unauthorized",
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}
                    },
                    str(HTTPStatus.FORBIDDEN.value): {
                        "description": "Forbidden",
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}
                    },
                    str(HTTPStatus.INTERNAL_SERVER_ERROR.value): {
                        "description": "Internal Server Error",
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}
                    }
                }
                
                if method_lower in ["get", "post", "put", "patch"] and hasattr(view_class, 'serializer_class') and view_class.serializer_class is not None:
                    response_schema_name = view_class.serializer_class.__name__
                    self.register_serializer_schema(view_class.serializer_class, response_schema_name)
                    response_spec[str(getattr(view_class, 'default_response_status', 200))]["content"] = {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{response_schema_name}"}
                        }
                    }
                
                operation_spec["responses"] = response_spec
                logger.debug(f"Documented responses for {method} {path}.")

                if route.requires_auth:
                    operation_spec["security"] = [{"bearerAuth": []}]

                self.paths[openapi_path][method_lower] = operation_spec
                logger.debug(f"Documented {method} {path}.")
                documented_methods_count += 1
            else:
                logger.warning(f"View {getattr(view_class, '__name__', 'N/A')} for path '{path}' lists method '{method}' but no callable handler method '{method_lower}' is defined. Skipping documentation for this method.")

        if documented_methods_count > 0:
            dispatcher.send("api_docs_route_documented", sender=self, route=route, path=path, documented_methods_count=documented_methods_count)
            logger.debug(f"Signal 'api_docs_route_documented' sent for path '{path}'. Documented methods: {documented_methods_count}.")
            return True
        else:
            dispatcher.send("api_docs_route_skipped", sender=self, route=route, reason="no_callable_methods")
            logger.debug(f"Signal 'api_docs_route_skipped' (no_callable_methods) sent for path '{path}'.")
            return False

    def _convert_path_to_openapi(self, path: str, variable_names: Dict[str, Any]) -> str:
        """Converts Lback path format to OpenAPI path format."""
        openapi_path = path
        for var_name in variable_names:
            openapi_path = openapi_path.replace(f"{{{var_name}:int}}", f"{{{var_name}}}")
            openapi_path = openapi_path.replace(f"{{{var_name}}}", f"{{{var_name}}}")
        return openapi_path

    def register_serializer_schema(self, serializer_class: Type[BaseModelSerializer], schema_name: str):
        """
        Generates an OpenAPI schema from a BaseModelSerializer and adds it to components.
        This implementation will inspect the serializer fields to build the schema.
        """
        if schema_name in self.components["schemas"]:
            logger.debug(f"Schema '{schema_name}' already registered. Skipping.")
            return

        logger.debug(f"Registering schema for serializer: {serializer_class.__name__} as {schema_name}.")
        dispatcher.send("api_docs_serializer_schema_registered", sender=self, serializer_class=serializer_class, schema_name=schema_name)

        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'model'):
            model = serializer_class.Meta.model
            for field_name, field_type_info in self._get_serializer_fields_info(serializer_class).items():
                schema["properties"][field_name] = field_type_info['schema_type']
                if field_type_info.get('required'):
                    schema["required"].append(field_name)

        self.components["schemas"][schema_name] = schema
        logger.info(f"Schema '{schema_name}' registered from serializer '{serializer_class.__name__}'.")
        dispatcher.send("api_docs_serializer_schema_registered_finished", sender=self, schema_name=schema_name)


    def _get_serializer_fields_info(self, serializer_class: Type[BaseModelSerializer]) -> Dict[str, Any]:
        """
        [PLACEHOLDER]
        This method needs to be implemented based on how your BaseModelSerializer
        defines its fields and their types.
        It should return a dictionary like:
        {
            "field_name": {
                "schema_type": {"type": "string", "format": "date-time"},
                "required": True
            },
            ...
        }
        """
        fields_info = {}
        temp_serializer = serializer_class() 
        if hasattr(temp_serializer, '_declared_fields'):
            for field_name, field_instance in temp_serializer._declared_fields.items():
                schema_type = {"type": "string"} 
                if hasattr(field_instance, 'field_type_name'):
                    if field_instance.field_type_name == 'int': schema_type = {"type": "integer"}
                    elif field_instance.field_type_name == 'bool': schema_type = {"type": "boolean"}

                fields_info[field_name] = {
                    "schema_type": schema_type,
                    "required": getattr(field_instance, 'required', False)
                }
        
        elif hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'model'):
            model = serializer_class.Meta.model
            for column in model.__table__.columns:
                schema_type = {"type": "string"} 
                if hasattr(column.type, 'python_type'):
                    if column.type.python_type is int: schema_type = {"type": "integer"}
                    elif column.type.python_type is str: schema_type = {"type": "string"}
                    elif column.type.python_type is bool: schema_type = {"type": "boolean"}

                fields_info[column.name] = {
                    "schema_type": schema_type,
                    "required": not column.nullable
                }

            if hasattr(model, '_sa_class_manager'):
                for prop_name, prop_obj in model._sa_class_manager.iter_properties():
                    if isinstance(prop_obj, RelationshipProperty):
                        related_model = prop_obj.argument
                        related_serializer_name = f"{related_model.__name__}Serializer" 
                        fields_info[prop_name] = {"schema_type": {"$ref": f"#/components/schemas/{related_serializer_name}"}}
                        if prop_obj.uselist: 
                            fields_info[prop_name] = {"schema_type": {"type": "array", "items": {"$ref": f"#/components/schemas/{related_serializer_name}"}}}

        return fields_info