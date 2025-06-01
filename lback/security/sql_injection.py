import re
import logging

logger = logging.getLogger(__name__)

class SQLInjectionProtection:
    """
    Provides utility methods to detect and prevent potential SQL Injection attacks
    by scanning input strings and dictionaries for suspicious patterns.

    This class offers a basic layer of protection by identifying common SQL keywords,
    operators, and attack signatures within user-provided data. It's intended to
    be used as a preliminary check before interacting with a database, complementing
    the use of parameterized queries (which is the primary defense against SQL injection).
    """
    SUSPICIOUS_PATTERNS = [
        r"(--|\#|;|/\*|\*/|xp_)", 
        r"(\b(OR|AND)\b\s+\d+=\d+)", 
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)",
        r"(\bDROP\b|\bALTER\b|\bCREATE\b|\bEXEC\b)", 
        r"(['\"]\s*or\s*['\"]?\d+['\"]?\s*=\s*['\"]?\d+)", 
    ]


    @classmethod
    def is_safe(cls, value: str) -> bool:
        """
        Checks if a given string value contains any suspicious patterns indicative of SQL Injection.

        This method iterates through predefined regular expressions. If any pattern is found
        within the input string (case-insensitive), it logs a warning and returns False.

        :param value: The string to be checked for SQL Injection patterns.
        :type value: str
        :returns: True if the string is considered safe (no suspicious patterns found), False otherwise.
        :rtype: bool
        """
        if not isinstance(value, str):
            return True
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL Injection pattern detected: {pattern} in value: {value}")
                return False
        return True


    @classmethod
    def validate_inputs(cls, data: dict) -> bool:
        """
        Validates all string values within a dictionary for potential SQL Injection patterns.

        This method is useful for checking incoming request data (e.g., form submissions, JSON payloads)
        before processing. It recursively checks string values, returning False immediately
        upon detection of any suspicious pattern.

        :param data: A dictionary containing input data to be validated.
        :type data: dict
        :returns: True if all string values in the dictionary are safe, False if any suspicious
                  SQL Injection pattern is found.
        :rtype: bool
        """
        for key, value in data.items():
            if isinstance(value, str) and not cls.is_safe(value):
                return False
        return True