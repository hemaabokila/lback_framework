import logging
from typing import Dict
from lback.core.config import Config 

logger = logging.getLogger(__name__)

class SecurityHeadersConfigurator:
    """
    Manages the configuration and application of various HTTP security headers
    to enhance the web application's defense against common web vulnerabilities.

    This class reads security header settings from the application's Config instance
    and prepares a dictionary of headers and their corresponding values. These headers
    are then typically applied to HTTP responses by a middleware.
    """


    def __init__(self, config: Config):
        """
        Initializes the SecurityHeadersConfigurator.

        It loads security header settings from the provided Config instance
        and immediately prepares the headers to be applied.

        :param config: The application Config instance containing all application settings,
                       including the 'SECURITY_HEADERS' dictionary.
        :type config: Config
        """
        self.config = config
        self.security_headers_settings = getattr(config, 'SECURITY_HEADERS', {}) 
        logger.debug(f"SecurityHeadersConfigurator: Loaded settings: {self.security_headers_settings}")
        self._headers_to_apply = self._prepare_headers()


    def _prepare_headers(self) -> Dict[str, str]:
        """
        Prepares a dictionary of HTTP security headers and their values based on
        the loaded configuration.

        For each header, it attempts to retrieve the value from `self.security_headers_settings`.
        If a specific header setting is not found in the config, a sensible and secure
        default value is used.

        :returns: A dictionary where keys are HTTP header names (e.g., "Content-Security-Policy")
                  and values are their corresponding string values.
        :rtype: Dict[str, str]
        """
        headers: Dict[str, str] = {}
        csp_policy = self.security_headers_settings.get(
            'CONTENT_SECURITY_POLICY',
            "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'self'; media-src 'none'; object-src 'none'; frame-ancestors 'none';"
        )

        if csp_policy is not None:
            headers["Content-Security-Policy"] = csp_policy
  
        xss_protection = self.security_headers_settings.get('X_XSS_PROTECTION', "1; mode=block") 
        if xss_protection is not None:
            headers["X-XSS-Protection"] = xss_protection

        x_frame_options = self.security_headers_settings.get('X_FRAME_OPTIONS', "DENY")

        if x_frame_options is not None:
            headers["X-Frame-Options"] = x_frame_options

        x_content_type_options = self.security_headers_settings.get('X_CONTENT_TYPE_OPTIONS', "nosniff")

        if x_content_type_options is not None:
            headers["X-Content-Type-Options"] = x_content_type_options

        hsts_policy = self.security_headers_settings.get('STRICT_TRANSPORT_SECURITY', "max-age=31536000; includeSubDomains")

        if hsts_policy is not None:
            headers["Strict-Transport-Security"] = hsts_policy

        referrer_policy = self.security_headers_settings.get('REFERRER_POLICY', "no-referrer")

        if referrer_policy is not None:
            headers["Referrer-Policy"] = referrer_policy
        
        permissions_policy = self.security_headers_settings.get('PERMISSIONS_POLICY')

        if permissions_policy is not None:
            headers["Permissions-Policy"] = permissions_policy

        cross_domain_policies = self.security_headers_settings.get('X_PERMITTED_CROSS_DOMAIN_POLICIES')

        if cross_domain_policies is not None:
            headers["X-Permitted-Cross-Domain-Policies"] = cross_domain_policies
        logger.debug(f"SecurityHeadersConfigurator: Prepared security headers: {headers}")
        return headers
    
    
    def get_headers(self) -> Dict[str, str]:
        """
        Returns the dictionary of HTTP security headers prepared by the configurator.
        These headers are ready to be added to an HTTP response.

        :returns: A dictionary of security headers (e.g., "Content-Security-Policy": "value").
        :rtype: Dict[str, str]
        """
        return self._headers_to_apply
