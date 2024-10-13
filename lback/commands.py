import os
import subprocess
from lback.migration import Migration
from lback.server import Server
import json
from datetime import datetime
from lback.user import User
from lback.product import Product

class Commands:
    def __init__(self, config, name=None):
        self.name = name
        self.migration = Migration(config)

    def startproject(self):
        project_path = self._get_project_path()

        if self._project_exists(project_path):
            print(f"The project '{self.name}' already exists!")
            return
        self._create_project_structure(project_path)
        self._create_admin_page(project_path)
        print(f"Project '{self.name}' created successfully!")

    def _get_project_path(self):
        return os.path.join(os.getcwd(), self.name)

    def _project_exists(self, project_path):
        return os.path.exists(project_path)

    def _create_project_structure(self, project_path):
        os.makedirs(project_path, exist_ok=True)
        self._create_file(os.path.join(project_path, '__init__.py'), "# New project\n")
        self._create_file(os.path.join(project_path, 'settings.py'), self._get_settings_content())
        self._create_file(os.path.join(project_path, 'urls.py'), self._get_project_urls())
        self._create_file(os.path.join(project_path, 'main.py'), self._get_project_main())
        self._create_file(os.path.join(project_path, 'config.py'), self._get_project_config())
        self._create_file(os.path.join(project_path, '.env'), self._get_project_env())
        os.makedirs(os.path.join(project_path, 'migrations'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'staticfiles'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'templates'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'tests'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'docs'), exist_ok=True)

    def _get_project_config(self):
        return (
'''
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t", "yes")
    DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///mydatabase.db")
    
    ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost").split(",") if host.strip()]

    @staticmethod
    def init_app(app):
        pass

    @classmethod
    def from_env(cls, env_file=".env"):
        load_dotenv(env_file)
        return cls()

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == "default_secret_key":
            raise ValueError("SECRET_KEY must be set properly; the default value is not secure.")
        
        if not cls.DATABASE_URI:
            raise ValueError("DATABASE_URI is invalid.")

        if not cls.ALLOWED_HOSTS:
            raise ValueError("ALLOWED_HOSTS must contain at least 'localhost'.")

# from config import Config
# app.config.from_object(Config)

if __name__ == "__main__":
    try:
        Config.validate()
        print("Configuration validated successfully.")
    except ValueError as e:
        print(f"Configuration error: {e}")


'''
        )
    
    def _get_project_urls(self):
            return (
                "# URLs project\n"
                "from flask import Flask\n\n"
                "app = Flask(__name__)\n"
                "@app.route('/')\n"
                "def home():\n"
                    "return 'Welcome to the main project!'\n"

            )
    def _get_project_env(self):
            return (
'''
SECRET_KEY=supersecretkey123
DEBUG=True
DATABASE_URI=sqlite:///mydatabase.db
ALLOWED_HOSTS=localhost,127.0.0.1
'''

            )
    
    def _get_project_main(self):
            return (
                "# main.py project\n"
                "from flask import Flask\n\n"
                "from app1.urls import app1_bp\n"
                "from app2.urls import app2_bp\n\n"
                "app = Flask(__name__)\n"
                "app.register_blueprint(app1_bp, url_prefix='/app1')\n"
                "app.register_blueprint(app2_bp, url_prefix='/app2')\n\n"
'''
from app1.middleware import SomeMiddleware
from app2.middleware import OtherMiddleware
from lback.middleware import MiddlewareManager 

middleware_manager = MiddlewareManager()


middleware_manager.add_middleware(SomeMiddleware())
middleware_manager.add_middleware(OtherMiddleware())

request = {}
response = {}


pre_response = middleware_manager.process_request(request)
if pre_response is None:

    response = middleware_manager.process_response(request, response)

print("Final response:", response)

'''
                'if __name__ == "__main__":\n'
                    "app.run(debug=True)\n"
    

            )
    
    def _get_settings_content(self):
            return (
'''
import os
from config import Config


SECRET_KEY = Config.SECRET_KEY
DEBUG = Config.DEBUG
DATABASE_URI = Config.DATABASE_URI
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')


SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG


INSTALLED_APPS = [
    'app1',
    'app2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app1.middleware.SomeMiddleware',
    'app2.middleware.OtherMiddleware',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_URI, 
    }
}


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': Config.LOGGING_LEVEL,
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': Config.LOGGING_LEVEL,
        },
    },
}


Config.validate()


'''

            )

    def startapp(self):
        app_path = self._get_app_path()

        if self._app_exists(app_path):
            print(f"The app '{self.name}' already exists!")
            return
        self._create_app_structure(app_path)
        self._create_admin_page(app_path)
        print(f"App '{self.name}' created successfully!")

    def _get_app_path(self):
        return os.path.join(os.getcwd(), self.name)

    def _app_exists(self, app_path):
        return os.path.exists(app_path)

    def _create_app_structure(self, app_path):
        os.makedirs(app_path, exist_ok=True)
        self._create_file(os.path.join(app_path, '__init__.py'), "# New app\n")
        self._create_file(os.path.join(app_path, 'models.py'), self._get_app_models())
        self._create_file(os.path.join(app_path, 'urls.py'), self._get_app_urls())
        self._create_file(os.path.join(app_path, 'middleware.py'), self._get_app_middleware())
        os.makedirs(os.path.join(app_path, 'templates'), exist_ok=True)
        os.makedirs(os.path.join(app_path, 'static'), exist_ok=True)

    def _get_app_models(self):
        return (
            "# Models for the app\n"
            "class ExampleModel:\n"
            "__tablename__ = 'example_model'\n\n"
            "def get_fields(self):\n"
                "return {"
                    "'id': 'Integer',\n"
                    "'name': 'String',\n"
                "}\n"
        )

    def _get_app_urls(self):
        return (
            "# URLs for the app\n"
            "from flask import Blueprint\n\n"
            "app_name_bp = Blueprint('app_name', __name__)\n\n"
            "@app_name_bp.route('/')\n"
            "def index():\n"
            "    return 'Welcome to the app'\n"
        )
    def _get_app_middleware(self):
        return (
'''
# app1/middleware.py
class SomeMiddleware:
    def process_request(self, request):
        print("Processing request in SomeMiddleware")
        return None

    def process_response(self, request, response):
        print("Processing response in SomeMiddleware")
        return response

# app2/middleware.py
class OtherMiddleware:
    def process_request(self, request):
        print("Processing request in OtherMiddleware")
        return None

    def process_response(self, request, response):
        print("Processing response in OtherMiddleware")
        return response

'''
        )

    def _create_file(self, file_path, content):
        with open(file_path, 'w') as f:
            f.write(content)

    def _create_admin_page(self, project_path):
        admin_path = os.path.join(project_path, 'admin')
        os.makedirs(admin_path, exist_ok=True)
        print(f"Creating admin page in {admin_path}")

        self._create_file(os.path.join(admin_path, '__init__.py'), "# Admin package\n")
        self._create_file(os.path.join(admin_path, 'views.py'), self._get_admin_views_content())
        self._create_file(os.path.join(admin_path, 'adminauth.py'), self._get_admin_auth_content())

    def _get_admin_views_content(self):
        return (
            "from lback.adminauth import AdminPage\n\n"
            "admin = AdminPage()\n"
            "@admin.route('/admin')\n"
            "def admin_home():\n"
                'return "Welcome to the Admin Page!"\n'
        )

    def _get_admin_auth_content(self):
        return (
            "from lback.adminauth import AdminAuth\n\n"
            "adminauth = AdminAuth()\n"
            "@adminauth.route('/login')\n"
            "def login():\n"
                'return "Login Page"\n'
        )

    def runserver(self):
        server = Server()
        try:
            server.start()
        except Exception as e:
            print(f"Error running server: {e}")

    def migrate(self):
        models = [User, Product]
        self.migration.apply(models)
        print("Migration completed successfully.")

    def makemigrations(self):
        models = [User, Product]
        migration_file = self.create_migration_file(models)
        if migration_file:
            print(f"Migration file created: {migration_file}")

    def create_migration_file(self, models):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        migration_file = f"migrations/{timestamp}_migration.json"
        os.makedirs(os.path.dirname(migration_file), exist_ok=True)

        migration_data = {}
        
        for model in models:
            table_name = model.__tablename__
            fields = model.get_fields()
            migration_data[table_name] = fields

        with open(migration_file, 'w') as f:
            json.dump(migration_data, f, ensure_ascii=False, indent=4)

        return migration_file

    def test(self):
        print("Running tests...")
        try:
            subprocess.run(["pytest"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running tests: {e}")

    def collectstatic(self):
        static_dir = os.path.join(os.getcwd(), 'staticfiles')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        print("Collecting static files...")

    def help(self):
        print("Available commands:")
        print("  startproject <project name>")
        print("  startapp <app name>")
        print("  runserver")
        print("  migrate")
        print("  makemigrations")
        print("  test")
        print("  collectstatic")










