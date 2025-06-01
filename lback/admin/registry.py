import logging
from typing import Dict, Type, Optional, Any

from lback.core.signals import dispatcher
from lback.models.base import BaseModel as Base


logger = logging.getLogger(__name__)

class AdminRegistry:
    """
    Registry for the standard administration application.
    Keeps track of models registered for administration.
    Integrates SignalDispatcher to emit events related to registry initialization and model registration.
    """
    def __init__(self):
        """
        Initializes the AdminRegistry.
        Emits 'admin_registry_initialized' signal.
        """
        self._registered_models: Dict[str, Type[Any]] = {}
        self._original_names_map: Dict[str, str] = {}
        logger.info("AdminRegistry initialized.")
        dispatcher.send("admin_registry_initialized", sender=self)
        logger.debug("Signal 'admin_registry_initialized' sent.")


    def register(self, model_class: Type[Any]):
        """
        Registers a model class with the admin registry.
        Stores the model using its lowercase name as the dictionary key.
        Emits 'admin_model_registered' signal on success.
        Emits 'admin_model_registration_failed' signal on failure (invalid model, already registered).

        Args:
            model_class: The SQLAlchemy model class to register.

        Raises:
            ValueError: If the registered model is not a valid model class,
                        or if the model is already registered (case-insensitive).
        """
        original_model_name = getattr(model_class, '__name__', 'N/A')
        lowercase_model_name = original_model_name.lower()

        logger.info(f"Attempting to register model '{original_model_name}' (lowercase: '{lowercase_model_name}') with AdminRegistry.")

        try:
            if not issubclass(model_class, Base):
                 logger.warning(f"Registration failed for '{original_model_name}': Not a valid BaseModel subclass.")
                 dispatcher.send("admin_model_registration_failed", sender=self, model_class=model_class, model_name=original_model_name, error_type="invalid_class")
                 logger.debug(f"Signal 'admin_model_registration_failed' (invalid_class) sent for '{original_model_name}'.")
                 raise ValueError(f"'{model_class.__name__}' is not a valid SQLAlchemy model class (must inherit from BaseModel).")

            if lowercase_model_name in self._registered_models:
                 logger.warning(f"Registration failed for '{original_model_name}': Model with lowercase name '{lowercase_model_name}' is already registered.")
                 dispatcher.send("admin_model_registration_failed", sender=self, model_class=model_class, model_name=original_model_name, error_type="already_registered")
                 logger.debug(f"Signal 'admin_model_registration_failed' (already_registered) sent for '{original_model_name}'.")
                 raise ValueError(f"Model '{original_model_name}' (lowercase '{lowercase_model_name}') is already registered.")

            self._registered_models[lowercase_model_name] = model_class
            self._original_names_map[original_model_name] = lowercase_model_name

            logger.info(f"Model '{original_model_name}' registered successfully in AdminRegistry with lowercase key '{lowercase_model_name}'.")
            dispatcher.send("admin_model_registered", sender=self, model_class=model_class, model_name=original_model_name, lowercase_name=lowercase_model_name)
            logger.debug(f"Signal 'admin_model_registered' sent for '{original_model_name}'.")

        except ValueError as e:
            raise e
        except Exception as e:
             logger.exception(f"An unexpected error occurred during registration for model '{original_model_name}'.")
             dispatcher.send("admin_model_registration_failed", sender=self, model_class=model_class, model_name=original_model_name, error_type="exception", exception=e)
             logger.debug(f"Signal 'admin_model_registration_failed' (exception) sent for '{original_model_name}'.")
             raise

    def get_model(self, model_name: str) -> Optional[Type[Any]]:
        """
        Retrieves a registered model class by its name (case-insensitive).
        Converts the input name to lowercase before lookup.

        Args:
            model_name: The name of the model class as a string.

        Returns:
            The model class if registered, otherwise None.
        """
        logger.debug(f"Fetching model '{model_name}' (case-insensitive lookup) from AdminRegistry.")
        lowercase_model_name = model_name.lower()
        model = self._registered_models.get(lowercase_model_name)
        logger.debug(f"Lookup for lowercase name '{lowercase_model_name}' returned: {model is not None}")
        return model

    def get_registered_models(self) -> Dict[str, Type[Any]]:
        """
        Retrieves a dictionary of all registered models, using the original model names as keys.
        This is useful for displaying in the UI with correct capitalization.
        """
        logger.debug("Getting all registered models from AdminRegistry (returning original names).")
        original_name_models: Dict[str, Type[Any]] = {}
        for original_name, lowercase_name in self._original_names_map.items():
            if lowercase_name in self._registered_models:
                 original_name_models[original_name] = self._registered_models[lowercase_name]
            else:
                 logger.warning(f"Original name '{original_name}' mapped to lowercase '{lowercase_name}' but not found in registered models.")

        if not original_name_models and self._registered_models:
             logger.warning("Original names map incomplete. Falling back to returning lowercase model names for UI.")
             return self._registered_models

        return original_name_models

admin = AdminRegistry()
