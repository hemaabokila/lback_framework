import os
import subprocess
import logging
import time

from lback.core.server import Server, initialize_core_components
from lback.core.config import Config

logger = logging.getLogger(__name__)

class RunnerCommands:
    def runserver(self):
        """
        Run the development server.
        Initializes core server components before running the server.
        """
        config = Config()
        allowed_hosts_list = getattr(config, 'ALLOWED_HOSTS')
        host = "127.0.0.1"
        port = 8000
        if allowed_hosts_list:
            first_host_entry = allowed_hosts_list[0]
            if isinstance(first_host_entry, str) and first_host_entry:
                try:
                    parts = first_host_entry.split(':')
                    host = parts[0]
                    if len(parts) > 1:
                        port_str = parts[1]
                        if port_str.isdigit():
                            port = int(port_str)
                        else:
                            logger.info(f"Warning: Invalid port in ALLOWED_HOSTS: {port_str}. Using default port {port}")
                    else:
                        logger.info(f"Info: Port not specified in ALLOWED_HOSTS entry '{first_host_entry}'. Using default port {port}.")
                except Exception as e:
                    logger.info(f"Error parsing ALLOWED_HOSTS entry '{first_host_entry}': {e}. Using default host/port.")
        else:
            logger.info(f"Warning: ALLOWED_HOSTS list is empty or not set. Using default host {host} and port {port}.")

        try:
            logger.info("Initializing core server components...")
            initialize_core_components()
            logger.info("Core server components initialized.")

            print(f"Starting server on http://{host}:{port}...")
            server = Server()
            start_time = time.time()
            server.run(host, port)
            elapsed_time = time.time() - start_time
            logger.info(f"Server stopped. Total runtime: {elapsed_time:.2f} seconds.")

        except Exception as e:
            logger.exception(f"Error starting server: {e}")

    def test(self, test_path=None):
        """Run tests using pytest."""
        try:
            command = ['pytest']
            if test_path:
                command.append(test_path)
            logger.info(f"Running tests with command: {' '.join(command)}")
            start_time = time.time()
            subprocess.run(command, check=True, shell=False)
            elapsed_time = time.time() - start_time
            logger.info(f"All tests passed successfully in {elapsed_time:.2f} seconds.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Tests failed: {e}")

        except FileNotFoundError:
            logger.error("pytest is not installed or not found in PATH.")


    def collectstatic(self, static_dirs=None, output_dir='staticfiles'):
        """Collect static files into a single directory."""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Static files directory created: {output_dir}")
            else:
                logger.info(f"Static files directory already exists: {output_dir}")

            static_dirs = static_dirs or ['static']
            for static_dir in static_dirs:
                if os.path.exists(static_dir):
                    for root, dirs, files in os.walk(static_dir):
                        for file in files:
                            src_file = os.path.join(root, file)
                            rel_path = os.path.relpath(src_file, static_dir)
                            dest_file = os.path.join(output_dir, rel_path)
                            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                            with open(src_file, 'rb') as src, open(dest_file, 'wb') as dest:
                                dest.write(src.read())
                            logger.info(f"Copied: {src_file} -> {dest_file}")
                else:
                    logger.warning(f"Static directory not found: {static_dir}")

            logger.info("Static files collected successfully.")

        except Exception as e:
            logger.exception(f"Error collecting static files: {e}")