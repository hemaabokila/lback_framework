import os
import logging


logger = logging.getLogger(__name__)

class AppCommands:
    def __init__(self, name):
        self.name = name

    def startapp(self):
        """Create a new app structure."""
        app_path = os.path.join(os.getcwd(), self.name)
        if os.path.exists(app_path):
            logger.error(f"The app '{self.name}' already exists!")
            return
        try:
            self._create_app_structure(app_path)
            logger.info(f"App '{self.name}' created successfully at {app_path}!")
        except Exception as e:
            logger.exception(f"Error creating app '{self.name}': {e}")

    def _create_app_structure(self, path):
        """Create the directory structure and copy templates."""
        os.makedirs(path, exist_ok=True)
        logger.info(f"Creating app structure at {path}...")
        self._copy_template('app_templates/__init__.py.template', os.path.join(path, '__init__.py'))
        self._copy_template('app_templates/models.py.template', os.path.join(path, 'models.py'))
        self._copy_template('app_templates/urls.py.template', os.path.join(path, 'urls.py'))
        self._copy_template('app_templates/views.py.template', os.path.join(path, 'views.py'))
        self._copy_template('app_templates/admin.py.template', os.path.join(path, 'admin.py'))
        self._copy_template('app_templates/serializers.py.template', os.path.join(path, 'serializers.py'))

    def _copy_template(self, template_path, destination_path):
        """Copy a template file to the destination path."""
        try:
            template_full_path = os.path.join(os.path.dirname(__file__), '..', 'conf', template_path)
            with open(template_full_path, 'r') as template_file:
                content = template_file.read()
            content = content.replace('{{ app_name }}', self.name)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            with open(destination_path, 'w') as destination_file:
                destination_file.write(content)
            logger.info(f"Copied template: {template_path} -> {destination_path}")
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
        except Exception as e:
            logger.exception(f"Error copying template {template_path} to {destination_path}: {e}")