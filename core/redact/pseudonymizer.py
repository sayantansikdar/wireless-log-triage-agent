import hashlib
import hmac
import os
from collections import defaultdict
from typing import Dict, List, Tuple

from core.redact.detectors import DETECTORS

class Pseudonymizer:
    def __init__(self, key: bytes = None):
        # Key comes from env var, defaulting to random bytes for the session if not set
        key_hex = os.environ.get("REDACT_HMAC_KEY")
        if key_hex:
            self.key = bytes.fromhex(key_hex)
        else:
            self.key = key or os.urandom(32)
            
        self.report_counts = defaultdict(int)

    def _hash_value(self, value: str, prefix: str) -> str:
        """Generate a consistent keyed-HMAC token like MAC_7f3a."""
        h = hmac.new(self.key, value.encode('utf-8'), hashlib.sha256).hexdigest()
        return f"{prefix}_{h[:4]}"

    def redact(self, text: str) -> str:
        """Redact sensitive identifiers from text, maintaining consistency."""
        redacted_text = text
        
        # We need to process non-overlapping matches.
        # Simple approach: find all matches, sort by start index descending, replace.
        replacements = []
        
        for detector in DETECTORS:
            for match in detector.pattern.finditer(text):
                if detector.group_idx > 0:
                    raw_val = match.group(detector.group_idx)
                    start, end = match.span(detector.group_idx)
                else:
                    raw_val = match.group(0)
                    start, end = match.span(0)
                    
                if detector.validator and not detector.validator(raw_val):
                    continue
                    
                # Skip if already a redacted token (idempotency check)
                if re.match(r'^[A-Z0-9]+_[0-9a-f]{4}$', raw_val):
                    continue
                    
                token = self._hash_value(raw_val, detector.name)
                replacements.append((start, end, token, detector.name))
                
        # Sort replacements descending by start position to avoid offset shifting
        replacements.sort(key=lambda x: x[0], reverse=True)
        
        # Filter overlapping replacements (taking the first one we see, which is the last in the string)
        # Actually it's better to just ensure no overlaps
        valid_replacements = []
        last_start = float('inf')
        for start, end, token, name in replacements:
            if end <= last_start:
                valid_replacements.append((start, end, token, name))
                last_start = start
                
        for start, end, token, name in valid_replacements:
            redacted_text = redacted_text[:start] + token + redacted_text[end:]
            self.report_counts[name] += 1
            
        return redacted_text

    def get_report(self) -> Dict[str, int]:
        """Return counts of redacted items by type."""
        return dict(self.report_counts)
        
    def reset_report(self):
        self.report_counts.clear()

import re
