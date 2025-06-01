import logging
from typing import Callable, Dict, List, Any, Optional


logger = logging.getLogger(__name__)

Receiver = Callable[..., Any]
ReceiverList = List[Receiver]

SignalRegistry = Dict[str, ReceiverList]

class SignalDispatcher:
    """
    Signal Dispatcher for the Lback framework.

    This class allows registering receivers (callable functions or methods) for specific signals,
    and dispatching signals to invoke all registered receivers.
    """

    def __init__(self):
        """Initializes the SignalDispatcher with an empty signal registry."""
        self._registry: SignalRegistry = {}
        logger.info("SignalDispatcher initialized.")

    def connect(self, signal_name: str, receiver: Receiver):
        """
        Registers a receiver function or method to a specific signal.

        Args:
            signal_name (str): The name of the signal to connect the receiver to.
            receiver (Callable): The function or method to be called when the signal is dispatched.
                                 Must be callable.
        """
        if not isinstance(signal_name, str) or not signal_name:
            logger.error(f"Invalid signal_name provided: '{signal_name}'. Must be a non-empty string.")
            return

        if not callable(receiver):
            logger.error(f"Invalid receiver provided for signal '{signal_name}': {receiver}. Must be callable.")
            return

        if signal_name not in self._registry:
            self._registry[signal_name] = []
            logger.debug(f"Created new entry for signal: '{signal_name}' in registry.")

        if receiver not in self._registry[signal_name]:
            self._registry[signal_name].append(receiver)
            logger.info(f"Connected receiver {receiver.__name__} to signal '{signal_name}'.")
        else:
            logger.warning(f"Receiver {receiver.__name__} is already connected to signal '{signal_name}'. Skipping.")


    def disconnect(self, signal_name: str, receiver: Receiver):
        """
        Unregisters a receiver function or method from a specific signal.

        Args:
            signal_name (str): The name of the signal to disconnect the receiver from.
            receiver (Callable): The function or method to be unregistered.
        """
        if not isinstance(signal_name, str) or not signal_name:
            logger.error(f"Invalid signal_name provided for disconnect: '{signal_name}'. Must be a non-empty string.")
            return

        if not callable(receiver):
            logger.error(f"Invalid receiver provided for signal '{signal_name}' disconnect: {receiver}. Must be callable.")
            return
        
        if signal_name in self._registry:
            try:
                self._registry[signal_name].remove(receiver)
                logger.info(f"Disconnected receiver {receiver.__name__} from signal '{signal_name}'.")
                if not self._registry[signal_name]:
                    del self._registry[signal_name]
                    logger.debug(f"Removed signal '{signal_name}' from registry as it has no more receivers.")
            except ValueError:
                logger.warning(f"Receiver {receiver.__name__} was not found connected to signal '{signal_name}'.")
        else:
            logger.warning(f"Signal '{signal_name}' not found in registry. Cannot disconnect receiver {receiver.__name__}.")


    def send(self, signal_name: str, sender: Optional[Any] = None, **kwargs: Any):
        """
        Dispatches a signal, invoking all receivers registered to it.

        Args:
            signal_name (str): The name of the signal to dispatch.
            sender (Any, optional): The object sending the signal. Typically the instance where the event occurred.
            **kwargs: Additional keyword arguments to pass to the receivers.

        Returns:
            list: A list of tuples containing each receiver and its return value or exception.
        """
        if not isinstance(signal_name, str) or not signal_name:
            logger.error(f"Invalid signal_name provided for send: '{signal_name}'. Must be a non-empty string.")
            return []

        logger.debug(f"Sending signal: '{signal_name}' from sender: {sender} with data: {kwargs}")

        results = []

        if signal_name in self._registry:
            for receiver in list(self._registry[signal_name]):
                try:
                    result = receiver(sender=sender, **kwargs)
                    results.append((receiver, result))
                    logger.debug(f"Successfully called receiver {receiver.__name__} for signal '{signal_name}'.")
                except Exception as e:
                    logger.error(f"Error calling receiver {receiver.__name__} for signal '{signal_name}': {e}", exc_info=True)
                    results.append((receiver, e))

        else:
            logger.debug(f"No receivers connected for signal: '{signal_name}'.")

        return results

dispatcher = SignalDispatcher()

