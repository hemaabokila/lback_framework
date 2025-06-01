
class Include:
    """Represents an include directive in urlpatterns."""
    def __init__(self, module_path: str, prefix: str = ''):
        """
        Args:
            module_path: The dotted path to the urls module to include (e.g., 'myapp.urls').
            prefix: The URL prefix to prepend to the included urls (e.g., '/myapp/').
        """
        if not isinstance(module_path, str) or not module_path:
             raise ValueError("Included module_path must be a non-empty string.")
        if not isinstance(prefix, str):
             raise ValueError("Include prefix must be a string.")

        if prefix and not prefix.startswith('/'):
            prefix = '/' + prefix
        if prefix and prefix != '/' and not prefix.endswith('/') and not prefix.endswith('}'):
             prefix += '/'


        self.module_path = module_path
        self.prefix = prefix

    def __repr__(self):
        return f"Include('{self.module_path}', prefix='{self.prefix}')"


def include(module_path: str, prefix: str = ''):
    """Helper function to create an Include object."""
    return Include(module_path, prefix=prefix)

