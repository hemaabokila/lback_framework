Installation
============

This guide will help you install and set up the **lback** framework on your local machine.

Requirements
------------

- Python 3.8+
- pip (Python package installer)
- virtualenv (optional but highly recommended for managing project dependencies in an isolated environment)

Installation Steps
------------------

Follow these steps to get lback up and running:

1. **Create and Activate a Virtual Environment (Recommended)**

It's good practice to create a virtual environment for your project. This keeps its dependencies separate from other Python projects.

    .. code-block:: bash

        # Create a virtual environment (e.g., named 'lback_env')
        python -m venv lback_env

        # Activate the virtual environment
        # On Windows:
        lback_env\Scripts\activate
        # On macOS and Linux:
        source lback_env/bin/activate

2. **Install lback from PyPI**

Once your virtual environment is activated (if you chose to use one), you can install lback using pip:

    .. code-block:: bash

        pip install lback

3. **create a progect**:

   .. code-block:: bash

       lback startproject myproject

   Replace ``myproject`` with your desired project name.

4. **Run initial setup**:

   .. code-block:: bash

       python manage.py makemigrations
       python manage.py migrate
       python manage.py createsuperuser
       python manage.py runserver



You should now be able to access the application in your browser at ``http://127.0.0.1:8000``.

