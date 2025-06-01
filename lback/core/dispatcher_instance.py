import logging
from .signals import SignalDispatcher

logger = logging.getLogger(__name__)

dispatcher = SignalDispatcher()
logger.info("Application-wide SignalDispatcher instance created.")
