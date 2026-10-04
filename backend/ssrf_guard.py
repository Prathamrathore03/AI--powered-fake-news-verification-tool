"""
SSRF Protection Guard for VERITO
Validates submitted URLs to prevent Server-Side Request Forgery attacks.
"""

import ipaddress
import socket
from urllib.parse import urlparse

# Explicit blocked hostnames
BLOCKED_HOSTNAMES = {
    'localhost',
    'ip6-localhost',
    'ip6-loopback',
}

# Private/reserved IP ranges that should never be contacted
BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),        # RFC1918 private
    ipaddress.ip_network('172.16.0.0/12'),      # RFC1918 private
    ipaddress.ip_network('192.168.0.0/16'),     # RFC1918 private
    ipaddress.ip_network('127.0.0.0/8'),        # Loopback
    ipaddress.ip_network('169.254.0.0/16'),     # Link-local (APIPA)
    ipaddress.ip_network('100.64.0.0/10'),      # CGNAT
    ipaddress.ip_network('0.0.0.0/8'),          # "This" network
    ipaddress.ip_network('192.0.0.0/24'),       # IETF Protocol Assignments
    ipaddress.ip_network('198.18.0.0/15'),      # Benchmark testing
    ipaddress.ip_network('198.51.100.0/24'),    # TEST-NET-2 (documentation)
    ipaddress.ip_network('203.0.113.0/24'),     # TEST-NET-3 (documentation)
    ipaddress.ip_network('240.0.0.0/4'),        # Reserved (future use)
    ipaddress.ip_network('::1/128'),            # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),           # IPv6 unique local
    ipaddress.ip_network('fe80::/10'),          # IPv6 link-local
]

ALLOWED_SCHEMES = {'http', 'https'}
MAX_URL_LENGTH = 2048


def validate_url(url: str) -> str | None:
    """
    Validate a URL for safety and format.
    Returns None if valid, or a human-readable error string if invalid.
    """
    if not url or not isinstance(url, str):
        return "URL is required."

    url = url.strip()

    if len(url) > MAX_URL_LENGTH:
        return f"URL exceeds maximum allowed length ({MAX_URL_LENGTH} characters)."

    try:
        parsed = urlparse(url)
    except Exception:
        return "URL could not be parsed. Please check the format."

    # Validate scheme
    if not parsed.scheme:
        return "URL must include a scheme (e.g., https://...)."

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return (
            f"URL scheme '{parsed.scheme}' is not allowed. "
            "Only http:// and https:// URLs are accepted."
        )

    # Validate hostname
    hostname = parsed.hostname
    if not hostname:
        return "URL must include a valid hostname."

    if hostname.lower() in BLOCKED_HOSTNAMES:
        return "Requests to localhost and loopback addresses are not allowed."

    # Try to resolve hostname to IP and check against blocked ranges
    try:
        addr = ipaddress.ip_address(hostname)
        error = _check_ip_blocked(addr)
        if error:
            return error
    except ValueError:
        # hostname is a domain name — resolve it
        try:
            resolved_ip = socket.gethostbyname(hostname)
            addr = ipaddress.ip_address(resolved_ip)
            error = _check_ip_blocked(addr)
            if error:
                return f"The hostname '{hostname}' resolves to a blocked IP address: {error}"
        except socket.gaierror:
            # Could not resolve - allow through (might be a valid domain that will fail at request time)
            pass
        except Exception:
            pass

    # Validate path is non-empty (optional but helpful)
    if not parsed.netloc:
        return "URL does not contain a valid network location."

    return None


def _check_ip_blocked(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str | None:
    """Check if an IP address falls within any blocked network range."""
    for network in BLOCKED_NETWORKS:
        try:
            if addr in network:
                return f"Requests to private/reserved IP ranges are not allowed (blocked: {network})."
        except TypeError:
            continue  # IPv4/IPv6 type mismatch — skip
    return None
