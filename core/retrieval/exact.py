import re
from typing import List, Tuple

def extract_exact_tokens(query: str) -> List[str]:
    """
    Extracts exact telecom tokens from a query to use as pre-filters.
    Examples of tokens:
    - Timers: T3410, T3412
    - Cause codes: #15, cause 15 (we extract '15')
    - Sections: 5.5.1.2.5
    """
    tokens = []
    
    # 1. Timers (e.g., T3410, T3346)
    timers = re.findall(r'\bT\d{4}\b', query, re.IGNORECASE)
    tokens.extend([t.upper() for t in timers])
    
    # 2. Sections (e.g., 5.5.1.2)
    sections = re.findall(r'\b\d+\.\d+(?:\.\d+)+\b', query)
    tokens.extend(sections)
    
    # 3. Cause codes (e.g., #15 or cause 15)
    causes_hash = re.findall(r'#(\d+)\b', query)
    causes_text = re.findall(r'(?:cause|reason|status|code)\s+(\d+)\b', query, re.IGNORECASE)
    
    for c in causes_hash + causes_text:
        # We can look for exactly the number or #number
        # In exact matching, we might want to ensure we don't just match any "15"
        # So we return the hash format for exact matching if the corpus has `#15`
        tokens.append(f"#{c}")
        
    return list(set(tokens))

def build_lancedb_filter(tokens: List[str]) -> str:
    """
    Builds a LanceDB SQL WHERE clause from exact tokens.
    Uses OR logic for now.
    """
    if not tokens:
        return ""
        
    # Example: text LIKE '%T3410%' OR text LIKE '%#15%'
    # Or match metadata fields like section = '5.5.1'
    
    clauses = []
    for token in tokens:
        # If token is a section, match the section metadata exactly, else search text
        if re.match(r'^\d+\.\d+(?:\.\d+)+$', token):
            clauses.append(f"section = '{token}'")
        else:
            clauses.append(f"text LIKE '%{token}%'")
            
    return " OR ".join(clauses)
