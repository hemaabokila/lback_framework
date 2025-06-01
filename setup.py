from setuptools import setup, find_packages
import os


def read(fname):
    """Reads the content of a file relative to the setup.py location."""
    file_path = os.path.join(os.path.dirname(__file__), fname)
    if not os.path.exists(file_path):
        return ""
    with open(file_path, encoding='utf-8') as f:
        return f.read()


NAME = 'lback_framework'
VERSION = '0.1.0'
DESCRIPTION = 'A modern and powerful Python web framework.'
LONG_DESCRIPTION = read('README.md') if os.path.exists('README.md') else DESCRIPTION
LONG_DESCRIPTION_CONTENT_TYPE = 'text/markdown'
URL = 'https://github.com/hemaabokila/lback_framework'
AUTHOR = 'Ibrahem Abokila'
AUTHOR_EMAIL = 'ibrahemabokila@gmail.com'
LICENSE = 'MIT'

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Operating System :: OS Independent',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

INSTALL_REQUIRES = [
    'alembic==1.15.2',
    'attrs==25.3.0',
    'bcrypt==4.3.0',
    'boltons==21.0.0',
    'bracex==2.5.post1',
    'certifi==2025.1.31',
    'cffi==1.17.1',
    'charset-normalizer==3.4.1',
    'click==8.1.8',
    'click-option-group==0.5.7',
    'colorama==0.4.6',
    'cryptography==44.0.2',
    'defusedxml==0.7.1',
    'Deprecated==1.2.18',
    'dill==0.4.0',
    'exceptiongroup==1.2.2',
    'face==24.0.0',
    'glom==22.1.0',
    'googleapis-common-protos==1.70.0',
    'greenlet==3.1.1',
    'idna==3.10',
    'importlib_metadata==7.1.0',
    'Jinja2==3.1.6',
    'jsonschema==4.23.0',
    'jsonschema-specifications==2025.4.1',
    'jwt==1.3.1',
    'Mako==1.3.10',
    'markdown-it-py==3.0.0',
    'MarkupSafe==3.0.2',
    'mdurl==0.1.2',
    'opentelemetry-api==1.25.0',
    'opentelemetry-exporter-otlp-proto-common==1.25.0',
    'opentelemetry-exporter-otlp-proto-http==1.25.0',
    'opentelemetry-instrumentation==0.46b0',
    'opentelemetry-instrumentation-requests==0.46b0',
    'opentelemetry-proto==1.25.0',
    'opentelemetry-sdk==1.25.0',
    'opentelemetry-semantic-conventions==0.46b0',
    'opentelemetry-util-http==0.46b0',
    'packaging==25.0',
    'pbr==6.1.1',
    'platformdirs==4.3.7',
    'protobuf==4.25.7',
    'pycparser==2.22',
    'Pygments==2.19.1',
    'PyJWT==2.10.1',
    'python-dotenv==1.1.0',
    'python-magic-bin==0.4.14',
    'python-multipart==0.0.20',
    'python-slugify==8.0.4',
    'PyYAML==6.0.2',
    'referencing==0.36.2',
    'requests==2.32.3',
    'rich==13.5.3',
    'rpds-py==0.24.0',
    'ruamel.yaml==0.18.10',
    'ruamel.yaml.clib==0.2.12',
    'setuptools==80.3.0',
    'slugify==0.0.1',
    'SQLAlchemy==2.0.40',
    'stevedore==5.4.1',
    'text-unidecode==1.3',
    'tomli==2.0.2',
    'tomlkit==0.13.2',
    'typing_extensions==4.13.1',
    'urllib3==2.4.0',
    'watchdog==6.0.0',
    'wcmatch==8.5.2',
    'websockets==15.0.1',
    'Werkzeug==3.1.3',
    'wrapt==1.17.2',
    'zipp==3.21.0',
]

EXTRAS_REQUIRE = {
    'testing': [
        'bandit==1.8.3',
        'coverage==7.8.0',
        'isort==6.0.1',
        'pytest==8.3.5',
        'mypy==1.15.0',
        'pylint==3.3.6',
    ],
    'dev': [
        'bandit==1.8.3',
        'coverage==7.8.0',
        'isort==6.0.1',
        'pytest==8.3.5',
        'mypy==1.15.0',
        'pylint==3.3.6',
        'flake8',
        'build',
        'twine',
    ],

}

ENTRY_POINTS = {
    'console_scripts': [
        'lback = lback.main:main',
    ],
}

PACKAGES = find_packages(where='.')


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    classifiers=CLASSIFIERS,
    packages=PACKAGES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points=ENTRY_POINTS,
    include_package_data=True,
    python_requires='>=3.8',
    zip_safe=False,
)