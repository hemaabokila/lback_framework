from lback.core.cache import Cache
import time

def test_set_and_get():
    cache = Cache()
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar"

def test_expiry():
    cache = Cache()
    cache.set("foo", "bar", ttl=1)
    time.sleep(2)
    assert cache.get("foo") is None

def test_delete():
    cache = Cache()
    cache.set("foo", "bar")
    cache.delete("foo")
    assert cache.get("foo") is None

def test_clear():
    cache = Cache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None

def test_has():
    cache = Cache()
    cache.set("x", 123)
    assert cache.has("x")
    cache.delete("x")
    assert not cache.has("x")