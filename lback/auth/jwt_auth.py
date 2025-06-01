import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from lback.core.signals import dispatcher


logger = logging.getLogger(__name__)

class JWTAuth:
    """
    Utility class for creating, decoding, and validating JSON Web Tokens (JWT).
    Supports both access and refresh tokens.
    Integrates SignalDispatcher to emit events related to token lifecycle and validation.
    """
    def __init__(self, secret: str, algorithm: str = "HS256", access_exp: int = 3600, refresh_exp: int = 86400):
        """
        Initializes the JWTAuth utility.

        Args:
            secret: The secret key used for signing and verifying tokens.
                    Keep this secret and secure.
            algorithm: The signing algorithm to use (default is HS256).
            access_exp: Expiration time for access tokens in seconds (default is 1 hour).
            refresh_exp: Expiration time for refresh tokens in seconds (default is 24 hours).
        """
        if not secret:
            logger.error("JWTAuth initialized with an empty secret. Tokens will not be secure.")

        self.secret = secret
        self.algorithm = algorithm
        self.access_exp = access_exp
        self.refresh_exp = refresh_exp
        logger.info(f"JWTAuth initialized with algorithm: {self.algorithm}, access expiry: {self.access_exp}s, refresh expiry: {self.refresh_exp}s")

    def create_access_token(self, payload: Dict[str, Any]) -> str:
        """
        Creates a new access token.
        Emits 'jwt_access_token_created' signal on creation.

        Args:
            payload: A dictionary containing the data to encode in the token.
                     Should NOT contain sensitive information like passwords.
                     A 'user_id' or similar identifier is common.

        Returns:
            A signed JWT access token string.
        """
        data = payload.copy()
        data["type"] = "access"
        data["exp"] = datetime.utcnow() + timedelta(seconds=self.access_exp)
        logger.debug(f"Creating access token with payload: {payload}")
        token = jwt.encode(data, self.secret, algorithm=self.algorithm)
        dispatcher.send("jwt_access_token_created", sender=self, payload=payload, token=token)
        logger.debug("Signal 'jwt_access_token_created' sent.")

        return token

    def create_refresh_token(self, payload: Dict[str, Any]) -> str:
        """
        Creates a new refresh token.
        Emits 'jwt_refresh_token_created' signal on creation.

        Args:
            payload: A dictionary containing the data to encode in the token.
                     Should contain information needed to issue a new access token,
                     like 'user_id'.

        Returns:
            A signed JWT refresh token string.
        """
        data = payload.copy()
        data["type"] = "refresh"
        data["exp"] = datetime.utcnow() + timedelta(seconds=self.refresh_exp)
        logger.debug(f"Creating refresh token with payload: {payload}")
        token = jwt.encode(data, self.secret, algorithm=self.algorithm)

        dispatcher.send("jwt_refresh_token_created", sender=self, payload=payload, token=token)
        logger.debug("Signal 'jwt_refresh_token_created' sent.")

        return token

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes a JWT token and verifies its signature and expiration.
        Emits 'jwt_token_decoded' on success.
        Emits 'jwt_decode_failed' on failure with specific error type.

        Args:
            token: The JWT token string to decode.

        Returns:
            A dictionary containing the decoded payload if valid, otherwise None.
        """
        if not token:
            logger.debug("Attempted to decode an empty token.")
            dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="empty_token", exception=None)
            logger.debug("Signal 'jwt_decode_failed' (empty_token) sent.")
            return None

        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            logger.debug(f"Successfully decoded token. Payload: {decoded}")
            dispatcher.send("jwt_token_decoded", sender=self, token=token, payload=decoded)
            logger.debug("Signal 'jwt_token_decoded' sent.")

            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired.")
            dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="expired", exception=None)
            logger.debug("Signal 'jwt_decode_failed' (expired) sent.")
            return None
        
        except jwt.InvalidSignatureError:
             logger.warning("JWT token has an invalid signature.")
             dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="invalid_signature", exception=None)
             logger.debug("Signal 'jwt_decode_failed' (invalid_signature) sent.")
             return None
        
        except jwt.InvalidAudienceError:
             logger.warning("JWT token has an invalid audience claim.")
             dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="invalid_audience", exception=None)
             logger.debug("Signal 'jwt_decode_failed' (invalid_audience) sent.")
             return None
        
        except jwt.InvalidIssuerError:
             logger.warning("JWT token has an invalid issuer claim.")
             dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="invalid_issuer", exception=None)
             logger.debug("Signal 'jwt_decode_failed' (invalid_issuer) sent.")
             return None
        
        except jwt.InvalidIssuedAtError:
             logger.warning("JWT token has an invalid issued at claim.")
             dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="invalid_issued_at", exception=None)
             logger.debug("Signal 'jwt_decode_failed' (invalid_issued_at) sent.")
             return None
        
        except jwt.DecodeError:
             logger.warning("JWT token decoding failed. Malformed token?")
             dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="decode_error", exception=None)
             logger.debug("Signal 'jwt_decode_failed' (decode_error) sent.")
             return None
        
        except Exception as e:
            logger.error(f"An unexpected error occurred during JWT token decoding: {e}", exc_info=True)
            dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="unexpected_exception", exception=e)
            logger.debug("Signal 'jwt_decode_failed' (unexpected_exception) sent.")
            return None

    def is_token_valid(self, token: str, token_type: Optional[str] = None) -> bool:
        """
        Checks if a JWT token is valid (signature and expiry) and optionally matches a specific type.
        This method primarily relies on decode_token, which emits failure signals.
        It adds a check for token type mismatch.

        Args:
            token: The JWT token string to validate.
            token_type: Optional. The expected type of the token ('access' or 'refresh').
                        If None, only checks signature and expiry.

        Returns:
            True if the token is valid and matches the type (if specified), False otherwise.
        """
        decoded = self.decode_token(token)
        if decoded is None:
            return False

        if token_type is not None:
            token_matches_type = decoded.get("type") == token_type

            if not token_matches_type:
                logger.debug(f"Token type mismatch. Expected '{token_type}', got '{decoded.get('type')}'.")
                dispatcher.send("jwt_decode_failed", sender=self, token=token, error_type="type_mismatch", expected_type=token_type, actual_type=decoded.get('type'))
                logger.debug("Signal 'jwt_decode_failed' (type_mismatch) sent.")
            return token_matches_type

        return True

    def get_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes a token and returns its payload if valid.
        Relies on decode_token for validation and signal emission.

        Args:
            token: The JWT token string.

        Returns:
            The decoded payload dictionary if the token is valid, otherwise None.
        """
        return self.decode_token(token)

    def get_user_id(self, token: str) -> Optional[Any]:
        """
        Decodes a token and returns the 'user_id' claim if the token is valid and the claim exists.
        Relies on decode_token for validation and signal emission.

        Args:
            token: The JWT token string.

        Returns:
            The value of the 'user_id' claim if found in a valid token, otherwise None.
        """
        decoded = self.decode_token(token)
        if decoded:
             return decoded.get("user_id")
        return None
