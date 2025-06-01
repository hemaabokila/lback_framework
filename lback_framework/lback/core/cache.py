import time
import threading
from typing import Any, Dict, Optional, List

from lback.core.signals import dispatcher

import logging
logger = logging.getLogger(__name__)

class CacheItem:
    """Represents an item stored in the cache with an optional expiration time."""
    def __init__(self, value: Any, expires_at: Optional[float] = None):
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Checks if the cache item has expired."""
        return self.expires_at is not None and time.time() > self.expires_at

class Cache:
    """
    A simple thread-safe in-memory cache with optional time-to-live (TTL).
    Integrates SignalDispatcher to emit events for cache operations.
    """
    def __init__(self):
        """
        Initializes the Cache.
        Emits 'cache_initialized' signal.
        """
        self._cache: Dict[Any, CacheItem] = {}
        self._lock = threading.Lock()
        logger.info("Cache initialized.")
        dispatcher.send("cache_initialized", sender=self)
        logger.debug("Signal 'cache_initialized' sent.")


    def set(self, key: Any, value: Any, ttl: Optional[int] = None):
        """
        Sets a key-value pair in the cache with an optional time-to-live (TTL).
        Emits 'cache_item_set' signal.

        Args:
            key: The cache key.
            value: The value to store.
            ttl (Optional[int]): The time-to-live in seconds. If None, the item does not expire.
        """
        expires_at = time.time() + ttl if ttl is not None else None
        logger.debug(f"Attempting to set cache key '{key}' with TTL: {ttl} seconds.")
        try:
            with self._lock:
                self._cache[key] = CacheItem(value, expires_at)
            logger.info(f"Cache key '{key}' set successfully.")
            dispatcher.send("cache_item_set", sender=self, key=key, ttl=ttl, expires_at=expires_at)
            logger.debug(f"Signal 'cache_item_set' sent for key '{key}'.")
        except Exception as e:
            logger.exception(f"Error setting cache key '{key}': {e}")

    def get(self, key: Any) -> Optional[Any]:
        """
        Retrieves a value from the cache by key.
        Handles expired items.
        Emits 'cache_item_fetched', 'cache_hit', 'cache_miss', and 'cache_item_expired' signals.

        Args:
            key: The cache key to retrieve.

        Returns:
            The value associated with the key, or None if the key is not found or expired.
        """
        logger.debug(f"Attempting to get cache key '{key}'.")
        item = None
        value = None
        outcome = "miss"

        try:
            with self._lock:
                item = self._cache.get(key)

                if not item:
                    logger.debug(f"Cache miss for key '{key}': Key not found.")
                    outcome = "miss"
                elif item.is_expired():
                    logger.debug(f"Cache miss for key '{key}': Item expired.")

                    dispatcher.send("cache_item_expired", sender=self, key=key, expires_at=item.expires_at)
                    logger.debug(f"Signal 'cache_item_expired' sent for key '{key}'.")
                    del self._cache[key]
                    outcome = "miss"
                else:
                    value = item.value
                    logger.debug(f"Cache hit for key '{key}'.")
                    outcome = "hit"

        except Exception as e:
            logger.exception(f"Error getting cache key '{key}': {e}")
            outcome = "error"

        dispatcher.send("cache_item_fetched", sender=self, key=key, outcome=outcome)
        logger.debug(f"Signal 'cache_item_fetched' sent for key '{key}'. Outcome: {outcome}.")

        if outcome == "hit":
             dispatcher.send("cache_hit", sender=self, key=key)
             logger.debug(f"Signal 'cache_hit' sent for key '{key}'.")
        elif outcome == "miss":
             dispatcher.send("cache_miss", sender=self, key=key)
             logger.debug(f"Signal 'cache_miss' sent for key '{key}'.")

        return value


    def delete(self, key: Any):
        """
        Deletes a key-value pair from the cache.
        Emits 'cache_item_deleted' signal if the key was found and deleted.

        Args:
            key: The cache key to delete.
        """
        logger.debug(f"Attempting to delete cache key '{key}'.")
        deleted = False
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    deleted = True
                    logger.info(f"Cache key '{key}' deleted successfully.")
                else:
                    logger.debug(f"Cache key '{key}' not found for deletion.")

            if deleted:
                 dispatcher.send("cache_item_deleted", sender=self, key=key)
                 logger.debug(f"Signal 'cache_item_deleted' sent for key '{key}'.")

        except Exception as e:
            logger.exception(f"Error deleting cache key '{key}': {e}")


    def clear(self):
        """
        Clears all items from the cache.
        Emits 'cache_cleared' signal.
        """
        logger.info("Attempting to clear the entire cache.")
        initial_count = len(self._cache)
        try:
            with self._lock:
                self._cache.clear()
            logger.info("Cache cleared successfully.")
            dispatcher.send("cache_cleared", sender=self, cleared_count=initial_count)
            logger.debug(f"Signal 'cache_cleared' sent. Cleared {initial_count} items.")

        except Exception as e:
            logger.exception(f"Error clearing cache: {e}")


    def has(self, key: Any) -> bool:
        """
        Checks if a key exists in the cache and is not expired.
        # No signals here, as this is a simple status check.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        logger.debug(f"Checking if cache key '{key}' exists and is not expired.")
        with self._lock:
            item = self._cache.get(key)
            exists_and_not_expired = item is not None and not item.is_expired()
            logger.debug(f"Cache key '{key}' exists and is not expired: {exists_and_not_expired}")
            return exists_and_not_expired


    def keys(self) -> List[Any]:
        """
        Returns a list of all non-expired keys currently in the cache.
        # No signals here, as this is a simple read operation.

        Returns:
            A list of cache keys.
        """
        logger.debug("Getting all non-expired cache keys.")
        with self._lock:
            active_keys = [k for k, v in self._cache.items() if not v.is_expired()]
            logger.debug(f"Found {len(active_keys)} non-expired cache keys.")
            return active_keys

