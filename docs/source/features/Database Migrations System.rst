.. _database_migrations:

Database Migrations System
==========================

Lback utilizes `Alembic`_ to manage database schema changes in an organized, version-controlled, and automated manner. This system allows you to:

* Keep your database schema in sync with your application's `SQLAlchemy`_ models.
* Track and revert changes incrementally.
* Collaborate on schema changes within a team effectively.

.. _Alembic: https://alembic.sqlalchemy.org/en/latest/
.. _SQLAlchemy: https://www.sqlalchemy.org/

Migration Commands
------------------

Your `manage.py` script provides convenient wrappers around Alembic commands for common migration tasks:

#. **Creating new migration files (`makemigrations`)**

   Use the ``makemigrations`` command to automatically detect changes in your SQLAlchemy models (e.g., new tables, added columns, changed column types) and generate a new migration script. This script contains the necessary Python code to apply (`upgrade`) and revert (`downgrade`) these schema changes.

   .. code-block:: bash

      python manage.py makemigrations <migration_name>

   * Replace ``<migration_name>`` with a descriptive name for your migration (e.g., ``add_users_table``, ``alter_products_price_column``). This name will be part of the generated file name and helps in understanding the migration's purpose.
   * A new Python file will be created in your migrations directory (e.g., ``migrations/versions/``) with a unique revision identifier and your chosen name.

#. **Applying pending migrations (`migrate`)**

   The ``migrate`` command applies any migration scripts that have not yet been run on your current database. This brings your database schema up to the latest version defined by your migration files.

   .. code-block:: bash

      python manage.py migrate

   * This command will execute the ``upgrade()`` function in each pending migration script, in order, updating your database schema.
   * It's crucial to run this command after pulling new changes from version control that include new migration files.

#. **Rolling back migrations (`rollback`)**

   The ``rollback`` command allows you to revert specific schema changes. This is particularly useful during development or when you need to undo a recent migration.

   .. code-block:: bash

      python manage.py rollback <table>

   * This command is designed to roll back the *latest* schema changes associated with a specific ``<table>``. The `manage.py` script will intelligently identify and revert the relevant migration(s) that impacted that table.
   * **Note**: Standard Alembic typically operates on revisions (e.g., ``alembic downgrade -1`` to go back one step). This `rollback <table>` syntax suggests a custom wrapper in your `manage.py` to simplify table-specific rollbacks, which is a powerful abstraction.

Development Workflow
--------------------

A typical development workflow involving database migrations looks like this:

1.  **Modify Models**: Make changes to your SQLAlchemy models (e.g., in `lback/models/`).
2.  **Generate Migration**: Run ``python manage.py makemigrations <descriptive_name>``.
3.  **Review Migration**: Open the generated migration file and review its `upgrade()` and `downgrade()` functions to ensure they correctly reflect your intended changes.
4.  **Apply Migration**: Run ``python manage.py migrate`` to apply the changes to your local development database.
5.  **Version Control**: Commit both your model changes and the newly generated migration file to your version control system (e.g., Git).

By following this process, you ensure that your database schema evolves in a controlled and reproducible manner across all development, testing, and production environments.