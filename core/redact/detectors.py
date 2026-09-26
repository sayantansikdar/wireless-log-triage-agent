import re
from typing import NamedTuple, Pattern

class Detector(NamedTuple):
    name: str
    pattern: Pattern
    # For context-keyed matches, the actual value is in a capture group
    group_idx: int = 0
    # Validation function
    validator: callable = None

def is_valid_ipv4(ip: str) -> bool:
    parts = ip.split('.')
    return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)

def luhn_checksum(digits: str) -> bool:
    """Verify Luhn checksum for a 15-digit string (IMEI)."""
    if not digits.isdigit() or len(digits) != 15:
        return False
    total = 0
    for i, digit_str in enumerate(reversed(digits)):
        digit = int(digit_str)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0

# MAC Addresses: aa:bb:cc:dd:ee:ff or aa-bb-cc-dd-ee-ff or aaaa.bbbb.cccc
# We avoid picking up timestamps like 12:34:56:78:90:12 by checking context, or we just accept false positive MACs for 6-part timestamps.
# In wireless logs, MACs are frequent, so standard regex is fine.
MAC_PATTERN = re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b|\b[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\b')

# IMSI: context-keyed 15 digits
IMSI_PATTERN = re.compile(r'(?i)\bimsi\s*[=:]\s*["\']?(\d{15})\b')

# IMEI: context-keyed 15 digits, validated by Luhn
IMEI_PATTERN = re.compile(r'(?i)\bimei\s*[=:]\s*["\']?(\d{15})\b')

# IPv4
IPV4_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

# Emails
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

# Phone: e.g. +1234567890
PHONE_PATTERN = re.compile(r'\B\+[1-9]\d{6,14}\b')

# SSID: context-keyed string
SSID_PATTERN = re.compile(r'(?i)\bssid\s*[=:]\s*["\']([^"\']+)["\']')

DETECTORS = [
    Detector("MAC", MAC_PATTERN),
    Detector("IMSI", IMSI_PATTERN, group_idx=1),
    Detector("IMEI", IMEI_PATTERN, group_idx=1, validator=luhn_checksum),
    Detector("IPV4", IPV4_PATTERN, validator=is_valid_ipv4),
    Detector("EMAIL", EMAIL_PATTERN),
    Detector("PHONE", PHONE_PATTERN),
    Detector("SSID", SSID_PATTERN, group_idx=1)
]
