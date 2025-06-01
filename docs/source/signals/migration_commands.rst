.. _migration-commands-signals:

Signals from MigrationCommands
==============================

The :py:class:`lback.core.management.commands.migration.MigrationCommands` class provides a wrapper for Alembic, allowing command-line management of database migrations. This utility emits signals at various stages of its operations, which are **highly valuable for CI/CD pipelines, automated testing, logging, and monitoring the state and outcomes of database schema changes.**

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Signal Name
     - Description
     - Arguments (`kwargs`)
   * - ``migration_commands_initialized``
     - Emitted immediately after the :py:class:`~lback.core.management.commands.migration.MigrationCommands` instance has been initialized.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class that sent the signal.
   * - ``alembic_command_started``
     - Emitted just before an Alembic command is executed via a subprocess.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.<br>``command`` (:py:class:`str`): The primary Alembic command (e.g., "revision", "upgrade", "downgrade").<br>``args`` (:py:class:`tuple` of :py:class:`str`): Additional arguments passed to the Alembic command.<br>``full_command`` (:py:class:`list` of :py:class:`str`): The complete command list prepared for subprocess execution.
   * - ``alembic_command_completed``
     - Emitted when an Alembic command successfully completes its execution.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.<br>``command`` (:py:class:`str`): The primary Alembic command that completed.<br>``args`` (:py:class:`tuple` of :py:class:`str`): Additional arguments passed.<br>``returncode`` (:py:class:`int`): The exit code of the Alembic subprocess (expected to be 0 for success).<br>``stdout`` (:py:class:`str`): The standard output from the Alembic command.<br>``stderr`` (:py:class:`str`): The standard error from the Alembic command.
   * - ``alembic_command_failed``
     - Emitted when an Alembic command fails to execute or returns a non-zero exit code.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.<br>``command`` (:py:class:`str`): The primary Alembic command that failed.<br>``args`` (:py:class:`tuple` of :py:class:`str`): Additional arguments passed.<br>``returncode`` (:py:class:`int` or :py:class:`None`): The exit code of the Alembic subprocess, if available.<br>``stdout`` (:py:class:`str`): The standard output from the Alembic command.<br>``stderr`` (:py:class:`str`): The standard error from the Alembic command.<br>``error_type`` (:py:class:`str` or :py:class:`None`): A string indicating the type of error (e.g., "non_zero_exit_code", "alembic_not_found", "exception").<br>``exception`` (:py:class:`Exception` or :py:class:`None`): The exception object if an unexpected error occurred.
   * - ``migration_makemigrations_command``
     - Emitted specifically when the `makemigrations` command (Alembic `revision --autogenerate`) is invoked.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.<br>``message`` (:py:class:`str`): The message provided for the migration (or "auto").
   * - ``migration_migrate_command``
     - Emitted specifically when the `migrate` command (Alembic `upgrade`) is invoked to apply migrations.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.<br>``version`` (:py:class:`str`): The target migration version (e.g., "head", a revision ID).
   * - ``migration_rollback_command``
     - Emitted specifically when the `rollback` command (Alembic `downgrade`) is invoked to revert migrations.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.<br>``version`` (:py:class:`str`): The target version for the downgrade (e.g., "-1" for one step back, or a revision ID).
   * - ``migration_history_command``
     - Emitted specifically when the `history` command (Alembic `history`) is invoked to display migration history.
     - ``sender`` (:py:class:`~lback.core.management.commands.migration.MigrationCommands`): The instance of the class.

