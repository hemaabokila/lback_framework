
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from jinja2.ext import InternationalizationExtension
import os
import logging
import gettext
from http import HTTPStatus
from typing import Optional, Callable, List, Dict, Any
import builtins

from .signals import dispatcher
from .config import Config
from lback.utils.filters import CUSTOM_FILTERS


logger = logging.getLogger(__name__)

def default_global_context():
    """Provides a default context dictionary for all templates."""
    return {
        "app_name": "Lback",
        "version": "1.0",
    }

def custom_uppercase(value):
    """Custom Jinja2 filter to convert a value to uppercase if it's a string."""
    return value.upper() if isinstance(value, str) else value

def custom_url_tag(name: str) -> str:
    """
    Custom Jinja2 global function to generate URLs based on route names.
    NOTE: This is a placeholder implementation. Replace with actual URL reversal logic.
    """
    logger.warning(f"Using placeholder URL for route name: {name}")
    return f"/url/{name}"


class TemplateRenderer:
    """
    Manages the rendering of templates using Jinja2.
    Supports loading templates from file system directories and optionally from a database.
    Integrates SignalDispatcher to emit events during the rendering process.
    """
    def __init__(
        self,
        config: Config,
        db_session: Optional[Any] = None,
        template_model: Optional[Any] = None,
        db_loader_func: Optional[Callable[[str, Optional[Any]], Optional[str]]] = None
    ):
        """
        Initializes the TemplateRenderer.

        Args:
            config: The application Config instance.
            db_session: Optional SQLAlchemy session for loading templates from DB.
            template_model: Optional SQLAlchemy model class for templates stored in DB.
            db_loader_func: Optional custom function to load template content from DB.
                            It should accept template_name (str) and db_session (Optional[Any])
                            and return template content (str) or None.
        """
        self.config = config
        self.template_dirs = self._get_template_dirs(config)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dirs),
            autoescape=select_autoescape(['html', 'xml']),
            auto_reload=getattr(config, 'DEBUG', False),
            extensions=[InternationalizationExtension]
        )

        self.template_model = template_model
        self.db_loader_func = db_loader_func
        self.db_session = db_session 

        locale_dir = os.path.join(os.getcwd(), getattr(config, "LOCALE_DIR", "locale"))

        lang = getattr(config, "LANG", os.getenv("LANG", "en"))
        logger.info(f"Attempting to set up translations for language: {lang} in locale directory: {locale_dir}")

        try:
            translations = gettext.translation('messages', localedir=locale_dir, languages=[lang], fallback=True)
            self.env.install_gettext_translations(translations)
            logger.info(f"Translations loaded and installed for language: {lang}")
        except FileNotFoundError:
            logger.warning(f"No translation file found for domain 'messages' for language '{lang}' in '{locale_dir}'. Installing null translations.")
            self.env.install_null_translations()
        except Exception as e:
            logger.exception(f"An unexpected error occurred during gettext setup for language '{lang}': {e}")
            self.env.install_null_translations()

        self.env.filters['custom_uppercase'] = custom_uppercase
        self.env.filters.update(CUSTOM_FILTERS)
        self.env.globals['url'] = custom_url_tag 
        self.env.globals.update(default_global_context())
        self.env.globals['attribute'] = builtins.getattr
        logger.debug("Added 'attribute' (Python's getattr) to Jinja2 globals.")
        logger.info("TemplateRenderer initialized successfully.")

    def _get_template_dirs(self, config: Config) -> List[str]:
        """
        Determines the list of template directories to load, based on settings.
        Includes default project templates, app templates, and framework templates.
        """
        template_dirs = []
        project_root = os.getcwd()
        project_templates_dir = os.path.join(project_root, 'templates')
        if os.path.isdir(project_templates_dir):
             template_dirs.append(project_templates_dir)
             logger.info(f"Added project template directory: {project_templates_dir}")
        else:
             logger.warning(f"Project template directory not found at: {project_templates_dir}")

        installed_apps = getattr(config, "INSTALLED_APPS", [])
        logger.debug(f"Checking template directories for installed apps: {installed_apps}")
        for app_name in installed_apps:
            app_template_dir = os.path.join(project_root, app_name, 'templates')
            if os.path.isdir(app_template_dir):
                template_dirs.append(app_template_dir)
                logger.info(f"Added app template directory: {app_template_dir} for app: {app_name}")
            elif app_name== "admin" or "auth_app":
                continue
            else:
                logger.warning(f"Template directory not found for app: {app_name} at {app_template_dir}")
        framework_templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        framework_templates_dir = os.path.normpath(framework_templates_dir)

        if os.path.isdir(framework_templates_dir):
             template_dirs.append(framework_templates_dir)
             logger.info(f"Added framework template directory: {framework_templates_dir}")
        else:
             logger.warning(f"Framework templates directory not found at: {framework_templates_dir}")


        if not template_dirs:
            logger.error("No template directories found or configured. Template rendering will likely fail.")
        else:
             template_dirs = list(dict.fromkeys(template_dirs))
             logger.info(f"Final template directories loaded (unique, in order): {template_dirs}")

        return template_dirs


    def render_to_string(self, template_name: str, **context: Any) -> str:
        """
        Renders a template from the file system to a string.
        Emits 'template_rendering_started' and 'template_rendered' or 'template_rendering_failed' signals.
        Raises TemplateNotFound or other exceptions on failure.
        """
        logger.debug(f"Attempting to render template to string: {template_name}")
        dispatcher.send("template_rendering_started", sender=self, template_name=template_name, context=context, source="filesystem_string")
        logger.debug(f"Signal 'template_rendering_started' sent for '{template_name}' (filesystem_string).")

        try:
            full_context = {**default_global_context(), **context}
            template = self.env.get_template(template_name)
            rendered_content = template.render(full_context)
            logger.info(f"Successfully rendered template to string: {template_name}")
            dispatcher.send("template_rendered", sender=self, template_name=template_name, context=full_context, rendered_content=rendered_content, source="filesystem_string")
            logger.debug(f"Signal 'template_rendered' sent for '{template_name}' (filesystem_string).")

            csrf_input_snippet_start = rendered_content.find('<input type="hidden" name="csrfmiddlewaretoken"')
            if csrf_input_snippet_start != -1:
                csrf_input_snippet_end = rendered_content.find('>', csrf_input_snippet_start) + 1
                if csrf_input_snippet_end == 0:
                    csrf_input_snippet_end = csrf_input_snippet_start + 100
            else:
                logger.info(f"CSRF hidden input not found in rendered content for '{template_name}'.")
            return rendered_content
        except TemplateNotFound:
            logger.error(f"Template not found during render to string: {template_name}")
            dispatcher.send("template_rendering_failed", sender=self, template_name=template_name, context=context, source="filesystem_string", error_type="not_found", exception=None)
            logger.debug(f"Signal 'template_rendering_failed' (not_found) sent for '{template_name}' (filesystem_string).")
            raise TemplateNotFound(template_name)
        except Exception as e:
            logger.exception(f"Error rendering template to string: {template_name}")
            dispatcher.send("template_rendering_failed", sender=self, template_name=template_name, context=context, source="filesystem_string", error_type="exception", exception=e)
            logger.debug(f"Signal 'template_rendering_failed' (exception) sent for '{template_name}' (filesystem_string).")
            raise e


    def load_template_from_db(self, template_name: str) -> Optional[str]:
        """
        Attempts to load template content from the database using a custom loader
        or a default model lookup.
        Emits 'db_template_loaded' or 'db_template_load_failed' signals.
        """
        logger.debug(f"Attempting to load template '{template_name}' from DB.")
        dispatcher.send("db_template_loading_started", sender=self, template_name=template_name)
        logger.debug(f"Signal 'db_template_loading_started' sent for '{template_name}'.")

        template_content = None
        load_successful = False
        load_exception = None

        try:
            if self.db_loader_func:
                try:
                    template_content = self.db_loader_func(template_name, self.db_session)
                    if template_content is not None:
                        logger.debug(f"Template '{template_name}' loaded from DB using custom loader.")
                        load_successful = True
                    else:
                        logger.warning(f"Custom DB loader returned None for template '{template_name}'.")
                except Exception as e:
                    logger.error(f"Error in custom DB loader for template '{template_name}': {e}", exc_info=True)
                    load_exception = e
            if not load_successful and not self.db_loader_func or (self.db_loader_func and template_content is None):
                 if not self.db_session or not self.template_model:
                      logger.warning("No DB session or template model provided for loading templates from DB. Cannot load from DB using default loader.")
                 else:
                      try:
                          template_record = self.db_session.query(self.template_model).filter_by(name=template_name).first()
                          if template_record and hasattr(template_record, 'content'):
                              logger.debug(f"Template '{template_name}' loaded from DB using default model loader.")
                              template_content = template_record.content
                              load_successful = True
                          else:
                              logger.warning(f"Template '{template_name}' not found in DB or missing 'content' attribute.")
                      except Exception as e:
                           logger.error(f"Error loading template from DB using default model loader: {e}", exc_info=True)
                           load_exception = e


        except Exception as e:
             logger.exception(f"An unexpected error occurred during DB template loading for '{template_name}': {e}")
             load_exception = e
             load_successful = False

        finally:
            if load_successful and template_content is not None:
                dispatcher.send("db_template_loaded", sender=self, template_name=template_name, content=template_content)
                logger.debug(f"Signal 'db_template_loaded' sent for '{template_name}'.")
            else:
                dispatcher.send("db_template_load_failed", sender=self, template_name=template_name, exception=load_exception)
                logger.debug(f"Signal 'db_template_load_failed' sent for '{template_name}'.")

        return template_content


    def render_template_from_db(self, template_name: str, **context: Any) -> Dict[str, Any]:
        """
        Loads and renders a template from the database to a dictionary response format.
        Emits 'template_rendering_started' and 'template_rendered' or 'template_rendering_failed' signals.
        """
        logger.debug(f"Attempting to render template '{template_name}' from DB.")
        dispatcher.send("template_rendering_started", sender=self, template_name=template_name, context=context, source="database")
        logger.debug(f"Signal 'template_rendering_started' sent for '{template_name}' (database).")

        template_content = self.load_template_from_db(template_name)

        if template_content is None:
            logger.error(f"Template content not found in DB for: {template_name}")
            dispatcher.send("template_rendering_failed", sender=self, template_name=template_name, context=context, source="database", error_type="not_found_in_db", exception=None)
            logger.debug(f"Signal 'template_rendering_failed' (not_found_in_db) sent for '{template_name}' (database).")

            return {
                "status_code": HTTPStatus.NOT_FOUND.value,
                "body": b"Template not found in DB",
                "headers": {"Content-Type": "text/plain; charset=utf-8"}
            }

        try:
            full_context = {**default_global_context(), **context}
            template = self.env.from_string(template_content)
            rendered_content = template.render(full_context)
            logger.info(f"Successfully rendered DB template: {template_name}")
            dispatcher.send("template_rendered", sender=self, template_name=template_name, context=full_context, rendered_content=rendered_content, source="database")
            logger.debug(f"Signal 'template_rendered' sent for '{template_name}' (database).")

            return {
                "status_code": HTTPStatus.OK.value,
                "body": rendered_content,
                "headers": {"Content-Type": "text/html; charset=utf-8"}
            }
        except Exception as e:
            logger.exception(f"Error rendering DB template from content for: {template_name}")
            dispatcher.send("template_rendering_failed", sender=self, template_name=template_name, context=context, source="database", error_type="exception", exception=e)
            logger.debug(f"Signal 'template_rendering_failed' (exception) sent for '{template_name}' (database).")

            return {
                "status_code": HTTPStatus.INTERNAL_SERVER_ERROR.value,
                "body": b"An error occurred while rendering the DB template.",
                "headers": {"Content-Type": "text/plain; charset=utf-8"}
            }

    def render_from_db_to_string(self, template_name: str, **context: Any) -> str:
        """
        Loads and renders a template from the database to a string.
        Emits 'template_rendering_started' and 'template_rendered' or 'template_rendering_failed' signals.
        Raises TemplateNotFound or other exceptions on failure.
        """
        logger.debug(f"Attempting to render template '{template_name}' from DB to string.")
        dispatcher.send("template_rendering_started", sender=self, template_name=template_name, context=context, source="database_string")
        logger.debug(f"Signal 'template_rendering_started' sent for '{template_name}' (database_string).")

        template_content = self.load_template_from_db(template_name)

        if template_content is None:
            logger.error(f"Template content not found in DB during render to string: {template_name}")
            dispatcher.send("template_rendering_failed", sender=self, template_name=template_name, context=context, source="database_string", error_type="not_found_in_db", exception=None)
            logger.debug(f"Signal 'template_rendering_failed' (not_found_in_db) sent for '{template_name}' (database_string).")
            raise TemplateNotFound(template_name)

        try:
            full_context = {**default_global_context(), **context}
            template = self.env.from_string(template_content)
            rendered_content = template.render(full_context)
            logger.info(f"Successfully rendered DB template to string: {template_name}")
            dispatcher.send("template_rendered", sender=self, template_name=template_name, context=full_context, rendered_content=rendered_content, source="database_string")
            logger.debug(f"Signal 'template_rendered' sent for '{template_name}' (database_string).")

            return rendered_content
        except Exception as e:
            logger.exception(f"Error rendering DB template to string from content for: {template_name}")
            dispatcher.send("template_rendering_failed", sender=self, template_name=template_name, context=context, source="database_string", error_type="exception", exception=e)
            logger.debug(f"Signal 'template_rendering_failed' (exception) sent for '{template_name}' (database_string).")
            raise e

