import bcrypt
import logging
import secrets 

logger = logging.getLogger(__name__)

class PasswordHasher:
    """
    Utility class for securely hashing and verifying passwords using bcrypt.
    Bcrypt is a strong, adaptive hashing algorithm.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes a plain text password using bcrypt.

        Args:
            password: The plain text password string.

        Returns:
            A string containing the bcrypt hashed password.

        Raises:
            Exception: If hashing fails (e.g., due to encoding issues).
        """
        if not isinstance(password, str):
             logger.error("PasswordHasher received non-string password for hashing.")
             raise TypeError("Password must be a string.")

        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}", exc_info=True)
            raise


    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verifies a plain text password against a bcrypt hashed password.

        Args:
            password: The plain text password string to verify.
            hashed: The bcrypt hashed password string retrieved from storage.

        Returns:
            True if the password matches the hash, False otherwise.

        Raises:
            Exception: If verification fails (e.g., due to encoding issues or invalid hash format).
        """
        if not isinstance(password, str) or not isinstance(hashed, str):
             logger.error("PasswordHasher received non-string input for verification.")
             return False

        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except ValueError:
             logger.warning("Invalid hash format provided for password verification.")
             return False
        except Exception as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False

    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """
        Generates a cryptographically strong, random string suitable for tokens (e.g., email verification).

        Args:
            length: The desired length of the token string.

        Returns:
            A random hexadecimal string of the specified length.
        """
        if not isinstance(length, int) or length <= 0:
            logger.error(f"Invalid length '{length}' provided for token generation. Must be a positive integer.")
            raise ValueError("Token length must be a positive integer.")
        try:
            return secrets.token_hex(length // 2)
        except Exception as e:
            logger.error(f"Error generating random token: {e}", exc_info=True)
            raise
