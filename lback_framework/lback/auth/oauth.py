import requests
import logging
from typing import Dict, Optional, Any
from urllib.parse import urlencode


from lback.core.signals import dispatcher


logger = logging.getLogger(__name__)

class OAuth2Auth:
    """
    Utility class for interacting with an OAuth2 provider using the Authorization Code Grant flow.
    Provides methods for generating authorization URLs, fetching access tokens, and refreshing tokens.
    Integrates SignalDispatcher to emit events related to the OAuth2 flow.
    """

    def __init__(self, client_id: str, client_secret: str, authorize_url: str, token_url: str, redirect_uri: str, scope: str = ""):
        """
        Initializes the OAuth2Auth utility.

        Args:
            client_id: The client ID obtained from the OAuth2 provider.
            client_secret: The client secret obtained from the OAuth2 provider. Keep this secure.
            authorize_url: The URL of the authorization endpoint of the OAuth2 provider.
            token_url: The URL of the token endpoint of the OAuth2 provider.
            redirect_uri: The redirect URI registered with the OAuth2 provider.
            scope: The requested scope(s) (space-separated string). Defaults to "".
        """
        if not all([client_id, client_secret, authorize_url, token_url, redirect_uri]):
             logger.error("OAuth2Auth initialized with missing required parameters.")

        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scope = scope
        logger.info("OAuth2Auth utility initialized.")


    def get_authorize_url(self, state: Optional[str] = None) -> str:
        """
        Generates the authorization URL to redirect the user to the OAuth2 provider.
        Emits 'oauth2_authorize_url_generated' signal.

        Args:
            state: An optional state parameter to maintain state between the request
                   and the callback. Recommended for CSRF protection.

        Returns:
            The full authorization URL string.
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        if self.scope:
            params["scope"] = self.scope
        if state:
            params["state"] = state


        query_string = urlencode(params)

        url = f"{self.authorize_url}?{query_string}"
        logger.debug(f"Generated authorization URL: {url}")

        dispatcher.send("oauth2_authorize_url_generated", sender=self, authorize_url=url, state=state, scope=self.scope)
        logger.debug("Signal 'oauth2_authorize_url_generated' sent.")

        return url

    def fetch_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchanges an authorization code for an access token and optionally a refresh token.
        Emits 'oauth2_token_fetched' on success.
        Emits 'oauth2_token_fetch_failed' on failure.

        Args:
            code: The authorization code received from the OAuth2 provider.

        Returns:
            A dictionary containing the token response from the provider if successful,
            otherwise None. Expected keys often include 'access_token', 'token_type',
            'expires_in', and optionally 'refresh_token'.
        """
        logger.debug(f"Attempting to fetch OAuth2 token with code: {code[:10]}...")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        token_data = None
        fetch_successful = False
        fetch_exception = None

        try:
            response = requests.post(self.token_url, data=data, timeout=10)

            response.raise_for_status()

            token_data = response.json()
            logger.info("Successfully fetched OAuth2 token.")
            logger.debug(f"Token response keys: {list(token_data.keys())}")
            fetch_successful = True

        except requests.exceptions.Timeout:
            logger.error("Timeout occurred while fetching OAuth2 token.")
            fetch_exception = "timeout"

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching OAuth2 token: {e.response.status_code} - {e.response.text}")
            fetch_exception = f"http_error_{e.response.status_code}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching OAuth2 token: {e}")
            fetch_exception = "request_error"

        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching OAuth2 token: {e}", exc_info=True)
            fetch_exception = "unexpected_exception"

        finally:

            if fetch_successful and token_data is not None:
                dispatcher.send("oauth2_token_fetched", sender=self, code=code, token_data=token_data)
                logger.debug("Signal 'oauth2_token_fetched' sent.")

            else:
                error_detail = fetch_exception if isinstance(fetch_exception, str) else fetch_exception 
                dispatcher.send("oauth2_token_fetch_failed", sender=self, code=code, error=error_detail)
                logger.debug(f"Signal 'oauth2_token_fetch_failed' sent with error: {fetch_exception}.")

        return token_data


    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Exchanges a refresh token for a new access token and optionally a new refresh token.
        Emits 'oauth2_token_refreshed' on success.
        Emits 'oauth2_token_refresh_failed' on failure.

        Args:
            refresh_token: The refresh token obtained previously.

        Returns:
            A dictionary containing the new token response if successful, otherwise None.
            Expected keys often include 'access_token', 'token_type', 'expires_in',
            and optionally a new 'refresh_token'.
        """
        logger.debug("Attempting to refresh OAuth2 token.")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        token_data = None
        refresh_successful = False
        refresh_exception = None

        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            logger.info("Successfully refreshed OAuth2 token.")
            logger.debug(f"Refresh token response keys: {list(token_data.keys())}")
            refresh_successful = True

        except requests.exceptions.Timeout:
            logger.error("Timeout occurred while refreshing OAuth2 token.")
            refresh_exception = "timeout"

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error refreshing OAuth2 token: {e.response.status_code} - {e.response.text}")
            refresh_exception = f"http_error_{e.response.status_code}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error refreshing OAuth2 token: {e}")
            refresh_exception = "request_error"

        except Exception as e:
            logger.error(f"An unexpected error occurred while refreshing OAuth2 token: {e}", exc_info=True)
            refresh_exception = "unexpected_exception"

        finally:

            if refresh_successful and token_data is not None:
                dispatcher.send("oauth2_token_refreshed", sender=self, old_refresh_token=refresh_token, new_token_data=token_data)
                logger.debug("Signal 'oauth2_token_refreshed' sent.")

            else:
                 error_detail = refresh_exception if isinstance(refresh_exception, str) else refresh_exception
                 dispatcher.send("oauth2_token_refresh_failed", sender=self, old_refresh_token=refresh_token, error=error_detail)
                 logger.debug(f"Signal 'oauth2_token_refresh_failed' sent with error: {refresh_exception}.")


        return token_data
