from lback.security.firewall import AdvancedFirewall
from lback.security.sql_injection import SQLInjectionProtection
from lback.security.xss_protection import XSSProtection
from lback.security.rate_limiter import RateLimiter
from lback.security.headers import SecurityHeaders

def test_firewall_blocks_ip():
    firewall = AdvancedFirewall()
    firewall.block_ip("192.168.1.1")
    assert firewall.is_blocked("192.168.1.1")

def test_sql_injection_protection():
    protector = SQLInjectionProtection()
    assert protector.is_malicious("SELECT * FROM users WHERE 1=1;") is True
    assert protector.is_malicious("normal input") is False

def test_xss_protection():
    xss = XSSProtection()
    assert xss.is_malicious("<script>alert('xss')</script>") is True
    assert xss.is_malicious("safe text") is False

def test_rate_limiter():
    limiter = RateLimiter(max_requests=2, window_seconds=1)
    assert limiter.allow_request("user1")
    assert limiter.allow_request("user1")
    assert not limiter.allow_request("user1")

def test_security_headers():
    headers = SecurityHeaders().get_headers()
    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers