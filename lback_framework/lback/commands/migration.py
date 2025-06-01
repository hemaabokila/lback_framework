import subprocess
import sys
import logging
import os


from lback.core.signals import dispatcher

logger = logging.getLogger(__name__)

class MigrationCommands:
    """
    Provides command-line interface commands for managing database migrations using Alembic.
    Wraps Alembic subprocess calls and integrates SignalDispatcher to emit events.
    """
    def __init__(self, config=None):
        """
        Initializes MigrationCommands.
        Emits 'migration_commands_initialized' signal.
        """
        self.config = config
        logger.info("MigrationCommands initialized.")
        dispatcher.send("migration_commands_initialized", sender=self)
        logger.debug("Signal 'migration_commands_initialized' sent.")


    def _run_alembic(self, command: str, *args: str) -> bool:
        """
        Runs an alembic command as a subprocess from the project root.
        Emits 'alembic_command_started', 'alembic_command_completed',
        and 'alembic_command_failed' signals.

        Args:
            command: The Alembic command (e.g., 'revision', 'upgrade', 'downgrade').
            *args: Additional arguments for the Alembic command.

        Returns:
            True if the Alembic command completed successfully (exit code 0), False otherwise.
        """
        alembic_executable = 'alembic'
        full_command = [alembic_executable, command] + list(args)
        command_str = ' '.join(full_command)
        logger.info(f"Running Alembic command: {command_str}")

        dispatcher.send("alembic_command_started", sender=self, command=command, args=args, full_command=full_command)
        logger.debug(f"Signal 'alembic_command_started' sent for command '{command}'.")

        process = None
        stdout, stderr = "", ""
        returncode = None
        success = False
        error_type = None
        exception = None

        try:
            process = subprocess.Popen(
                full_command,
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate()
            returncode = process.returncode

            if stdout:
                print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)

            if returncode != 0:
                logger.error(f"Alembic command '{command}' failed with exit code {returncode}")
                success = False
                error_type = "non_zero_exit_code"
            else:
                logger.info(f"Alembic command '{command}' completed successfully.")
                success = True

        except FileNotFoundError:
            logger.error(f"Alembic executable not found. Make sure Alembic is installed in your virtual environment.")
            print("\nError: Alembic executable not found. Have you installed Alembic? (pip install alembic)", file=sys.stderr)
            success = False
            error_type = "alembic_not_found"

        except Exception as e:
            logger.exception(f"An unexpected error occurred while running Alembic command '{command}': {e}")
            success = False
            error_type = "exception"
            exception = e

        if success:
            dispatcher.send("alembic_command_completed", sender=self, command=command, args=args, returncode=returncode, stdout=stdout, stderr=stderr)
            logger.debug(f"Signal 'alembic_command_completed' sent for command '{command}'.")
            
        else:
            dispatcher.send("alembic_command_failed", sender=self, command=command, args=args, returncode=returncode, stdout=stdout, stderr=stderr, error_type=error_type, exception=exception)
            logger.debug(f"Signal 'alembic_command_failed' sent for command '{command}'. Error Type: {error_type}.")

        return success


    def makemigrations(self, message: str = "auto"):
        """
        Creates a new migration script based on model changes using Alembic.
        Emits 'migration_makemigrations_command' signal.
        """
        logger.info("Creating new migration script...")
        dispatcher.send("migration_makemigrations_command", sender=self, message=message)
        logger.debug("Signal 'migration_makemigrations_command' sent.")

        args = ["--autogenerate"]
        if message and message != "auto":
             args.extend(["-m", message])


        self._run_alembic("revision", *args)


    def migrate(self, version: str = "head"):
        """
        Applies pending migrations to the database using Alembic.
        Emits 'migration_migrate_command' signal.
        """
        logger.info(f"Applying migrations up to version: {version}")
        dispatcher.send("migration_migrate_command", sender=self, version=version)
        logger.debug("Signal 'migration_migrate_command' sent.")

        self._run_alembic("upgrade", version)

    def rollback(self, version: str = "-1"):
        """
        Rolls back migrations using Alembic.
        Emits 'migration_rollback_command' signal.
        """
        logger.info(f"Rolling back migrations to version: {version}")
        dispatcher.send("migration_rollback_command", sender=self, version=version)
        logger.debug("Signal 'migration_rollback_command' sent.")

        self._run_alembic("downgrade", version)


    def history(self):
        """
        Shows the migration history using Alembic.
        Emits 'migration_history_command' signal.
        """
        logger.info("Showing migration history...")
        dispatcher.send("migration_history_command", sender=self)
        logger.debug("Signal 'migration_history_command' sent.")

        self._run_alembic("history")

