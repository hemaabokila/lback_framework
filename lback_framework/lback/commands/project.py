import os
import logging


logger = logging.getLogger(__name__)

class ProjectCommands:
    def __init__(self, config, name):
        self.name = name
        self.config = config

    def startproject(self):
        """Create a new project structure."""
        project_path = os.path.join(os.getcwd(), self.name)
        if os.path.exists(project_path):
            logger.error(f"The project '{self.name}' already exists!")
            return
        try:
            self._create_project_structure(project_path)
            logger.info(f"Project '{self.name}' created successfully at {project_path}!")
        except Exception as e:
            logger.exception(f"Error creating project '{self.name}': {e}")

    def _create_project_structure(self, path):
        """Create the directory structure and copy templates."""
        os.makedirs(path, exist_ok=True)
        logger.info(f"Creating project structure at {path}...")

        self._copy_template('project_templates/__init__.py.template', os.path.join(path, '__init__.py'))
        self._copy_template('project_templates/urls.py.template', os.path.join(path, 'urls.py'))
        self._copy_template('project_templates/wsgi.py.template', os.path.join(path, 'wsgi.py'))

        alembic_dir_path = os.path.join(os.path.dirname(path), 'alembic')
        os.makedirs(alembic_dir_path, exist_ok=True)

        manage_py_path = os.path.join(os.path.dirname(path), 'manage.py')
        self._copy_template('project_templates/manage.py.template', manage_py_path)

        settings_py_path = os.path.join(os.path.dirname(path), 'settings.py')
        self._copy_template('project_templates/settings.py.template', settings_py_path)

        alembic_env_py = os.path.join(os.path.dirname(path), 'alembic/env.py')
        self._copy_template('alembic_template/env.py.template', alembic_env_py)

        alembic_script = os.path.join(os.path.dirname(path), 'alembic/script.py.mako')
        self._copy_template('alembic_template/script.py.mako.template', alembic_script)

        folder_name = 'versions'
        folder_path = os.path.join(alembic_dir_path, folder_name)

        alembic_ini_path = os.path.join(os.path.dirname(path), 'alembic.ini')
        self._copy_template('alembic_template/alembic.ini.template', alembic_ini_path)

        env_py = os.path.join(os.path.dirname(path), '.env')
        self._copy_template('project_templates/env.template', env_py)

        admin_logo = os.path.join(os.path.dirname(path), 'static/Lback_Logo.png')
        self._copy_template('project_templates/Lback_Logo.png', admin_logo)

        admin_css = os.path.join(os.path.dirname(path), 'static/css/tailwind.min.css')
        self._copy_template('project_templates/tailwind.min.css', admin_css)

        try:
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Empty folder '{folder_name}' created successfully inside 'alembic' at: {folder_path}")
        except OSError as e:
            logger.error(f"Error creating folder '{folder_name}' inside 'alembic': {e}")

    
    def _copy_template(self, template_path, destination_path):
        """Copy a template file to the destination path."""
        try:
            template_full_path = os.path.join(os.path.dirname(__file__), '..', 'conf', template_path)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            if template_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', 'css')):
                with open(template_full_path, 'rb') as template_file:
                    content = template_file.read()
                with open(destination_path, 'wb') as destination_file:
                    destination_file.write(content)
                logger.info(f"Copied binary template: {template_path} -> {destination_path}")
                
            else:
                with open(template_full_path, 'r') as template_file:
                    content = template_file.read()
                content = content.replace('{{ project_name }}', self.name)
                with open(destination_path, 'w') as destination_file:
                    destination_file.write(content)
                logger.info(f"Copied text template: {template_path} -> {destination_path}")

        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
            
        except Exception as e:
            logger.exception(f"Error copying template {template_path} to {destination_path}: {e}")