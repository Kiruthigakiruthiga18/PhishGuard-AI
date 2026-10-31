
from urllib.parse import urlparse
from collections import Counter
import ipaddress
import math
import re


SUSPICIOUS_WORDS = [
    "login", "verify", "account", "update",
    "secure", "banking", "password", "signin",
    "confirm", "wallet", "suspended"
]

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd",
    "shorturl.at", "rb.gy", "cutt.ly"
}


def extract_features(url):
    url = str(url).strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    # Add a default scheme if the URL has no scheme
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    url_lower = url.lower()
    hostname_lower = hostname.lower()

    # Check whether the hostname is an IP address
    try:
        ipaddress.ip_address(hostname)
        has_ip = 1
    except ValueError:
        has_ip = 0

    # Check whether the URL contains a port
    try:
        port = parsed.port
        has_port = int(port is not None)
    except ValueError:
        has_port = 1

    # Calculate URL entropy
    try:
        url_entropy = -sum(
            (count / len(url)) * math.log2(count / len(url))
            for count in Counter(url).values()
        )
    except (ValueError, ZeroDivisionError):
        url_entropy = 0.0

    # Count subdomains, ignoring a leading "www"
    domain_parts = hostname_lower.split(".")

    if domain_parts and domain_parts[0] == "www":
        domain_parts = domain_parts[1:]

    subdomain_count = max(0, len(domain_parts) - 2)

    # Count suspicious words found in the URL
    suspicious_word_count = sum(
        word in url_lower for word in SUSPICIOUS_WORDS
    )

    # Check whether the hostname is a known URL shortener
    shortener_match = int(
        hostname_lower in SHORTENER_DOMAINS
        or any(
            hostname_lower.endswith("." + domain)
            for domain in SHORTENER_DOMAINS
        )
    )

    # Extract the 22 URL features
    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),
        "dot_count": url.count("."),
        "hyphen_count": url.count("-"),
        "at_count": url.count("@"),
        "question_mark_count": url.count("?"),
        "ampersand_count": url.count("&"),
        "equals_count": url.count("="),
        "percent_count": url.count("%"),
        "digit_count": sum(char.isdigit() for char in url),
        "letter_count": sum(char.isalpha() for char in url),
        "https": int(parsed.scheme.lower() == "https"),
        "has_ip": has_ip,
        "subdomain_count": subdomain_count,
        "path_segment_count": len(
            [part for part in path.split("/") if part]
        ),
        "suspicious_word_count": suspicious_word_count,
        "is_shortener": shortener_match,
        "has_punycode": int("xn--" in hostname_lower),
        "has_port": has_port,
        "url_entropy": round(url_entropy, 4),
    }

    return features


if __name__ == "__main__":
    test_urls = [
        "https://www.google.com",
        "https://google.com",
        "http://192.168.1.10/login/verify?user=123",
        "https://secure-account-example.com/signin",
        "https://www.aap.org",
        "https://aap.org",
        "https://example.com",
    ]

    for test_url in test_urls:
        print("\nURL:", test_url)

        for name, value in extract_features(test_url).items():
            print(f"{name}: {value}")

        print("-" * 40)
