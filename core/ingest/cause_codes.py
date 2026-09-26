import re
from typing import Dict, Optional, List

def extract_cause_codes_from_markdown(md_text: str) -> Dict[str, str]:
    """
    Deterministically extract cause codes from Markdown tables.
    Returns a dictionary mapping cause code string (e.g. "3" or "#15") to its description.
    """
    cause_codes = {}
    
    # Simple markdown table row parser
    # Looks for lines starting with | and containing at least one more |
    table_row_pattern = re.compile(r'^\s*\|(.*)\|\s*$', re.MULTILINE)
    
    in_table = False
    headers = []
    
    for match in table_row_pattern.finditer(md_text):
        row = match.group(1)
        # Split by | and clean up whitespace
        cells = [cell.strip() for cell in row.split('|')]
        
        # Check for separator row (e.g. |---|---|)
        if all(re.match(r'^[-:]+$', c) for c in cells if c):
            continue
            
        if not in_table:
            # We assume the first row we see is a header
            headers = [c.lower() for c in cells]
            # Verify it looks like a cause code table
            if any("cause" in h or "reason" in h or "status" in h or "value" in h for h in headers):
                in_table = True
        else:
            # We are in a table, try to extract code and description
            if len(cells) >= 2:
                # Typically code is column 0, description is column 1
                # But sometimes there are more columns. Let's just take col 0 and the rest
                code_raw = cells[0]
                # Clean up the code (remove HTML tags, extra spaces)
                code_clean = re.sub(r'<[^>]+>', '', code_raw).strip()
                
                # Match numbers or numbers with # (e.g., "15", "#15", "0000 1111")
                # Some tables have binary, but standard EMM/5GMM causes use integers in the text
                # We'll just store the raw cleaned string as the key
                desc = " | ".join(cells[1:])
                desc_clean = re.sub(r'<[^>]+>', '', desc).strip()
                
                if code_clean and desc_clean:
                    cause_codes[code_clean] = desc_clean
                    # If it's a number, also store the # version
                    if code_clean.isdigit():
                        cause_codes[f"#{code_clean}"] = desc_clean
                        
    return cause_codes
