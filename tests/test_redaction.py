import pytest
from core.redact.pseudonymizer import Pseudonymizer
from core.redact.detectors import luhn_checksum

def test_luhn_checksum():
    assert luhn_checksum("353456789012348") == True
    assert luhn_checksum("353456789012345") == False
    assert luhn_checksum("not15digits") == False

def test_mac_redaction():
    p = Pseudonymizer(key=b"test_key")
    text = "Found device at aa:bb:cc:dd:ee:ff and 00:11:22:33:44:55."
    redacted = p.redact(text)
    assert "aa:bb:cc:dd:ee:ff" not in redacted
    assert "00:11:22:33:44:55" not in redacted
    assert "MAC_" in redacted
    
    # False positive trap: 6-part timestamp shouldn't break the world, 
    # but ideally it's ignored or just accepted as a MAC shape.
    # Our simple regex will catch 12:34:56:78:90:12 as a MAC, which is acceptable 
    # over-redaction for privacy.

def test_imsi_redaction():
    p = Pseudonymizer(key=b"test_key")
    # Context keyed
    text = "Connection from imsi=123456789012345 rejected."
    redacted = p.redact(text)
    assert "123456789012345" not in redacted
    assert "IMSI_" in redacted
    
    # 15 digit counter without context should NOT be redacted as IMSI
    text_no_context = "Counter reached 123456789012345."
    assert p.redact(text_no_context) == text_no_context

def test_imei_redaction():
    p = Pseudonymizer(key=b"test_key")
    # Valid Luhn IMEI
    text = "Device imei:353456789012348 attached."
    redacted = p.redact(text)
    assert "353456789012348" not in redacted
    assert "IMEI_" in redacted
    
    # Invalid Luhn IMEI
    text_invalid = "Device imei:353456789012346 attached."
    assert p.redact(text_invalid) == text_invalid

def test_idempotency():
    p = Pseudonymizer(key=b"test_key")
    text = "MAC aa:bb:cc:dd:ee:ff"
    redacted1 = p.redact(text)
    # Redacting again shouldn't double-redact
    redacted2 = p.redact(redacted1)
    assert redacted1 == redacted2

def test_report():
    p = Pseudonymizer(key=b"test_key")
    p.redact("MAC aa:bb:cc:dd:ee:ff and imsi=123456789012345")
    counts = p.get_report()
    assert counts["MAC"] == 1
    assert counts["IMSI"] == 1
