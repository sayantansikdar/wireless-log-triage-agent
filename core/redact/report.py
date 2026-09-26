import json
from typing import Dict

def generate_redaction_report(counts: Dict[str, int]) -> str:
    """
    Generate an audit report of redacted identifiers.
    Returns a JSON string of counts, containing no raw values.
    """
    report = {
        "status": "success",
        "redacted_items": counts,
        "total_redactions": sum(counts.values())
    }
    return json.dumps(report, indent=2)
