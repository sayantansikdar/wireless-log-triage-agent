import hashlib
from typing import Dict, List, Any
from core.ingest.parse_3gpp import Section

def generate_chunk_id(spec: str, version: str, section: str, chunk_index: int = 0) -> str:
    """Generate a stable, unique chunk ID."""
    key = f"{spec}_{version}_{section}_{chunk_index}"
    return hashlib.sha1(key.encode()).hexdigest()[:12]

def chunk_section(section: Section, max_chars: int = 2000, overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Chunks a section's content. 
    If the content is small, returns a single chunk.
    If it's large, splits it, but avoids splitting markdown tables.
    """
    # For now, simple split if over max_chars, but keeping tables intact is complex.
    # We will prioritize keeping it as a single chunk if it contains tables,
    # or just relying on LanceDB's large context window.
    # 3GPP sections are usually concise enough to fit in a single chunk unless they are massive tables.
    
    # A robust implementation would parse the markdown AST. 
    # For this baseline structure-aware chunking, we will yield the entire section as one chunk
    # unless it's obscenely long (e.g. > 4000 chars), then we naively split but try to avoid tables.
    
    text = section.content
    chunks = []
    
    if len(text) <= max_chars * 2:
        # Just use one chunk to preserve all tables and structure
        chunks.append(text)
    else:
        # Naive split for massive sections, with a basic heuristic to avoid splitting inside a table
        # (A table line usually starts with '|')
        lines = text.split('\n')
        current_chunk = []
        current_len = 0
        
        for line in lines:
            current_chunk.append(line)
            current_len += len(line) + 1
            
            if current_len > max_chars and not line.strip().startswith('|'):
                chunks.append('\n'.join(current_chunk))
                # keep overlap
                overlap_lines = current_chunk[-5:] if len(current_chunk) > 5 else current_chunk
                current_chunk = overlap_lines
                current_len = sum(len(l) + 1 for l in overlap_lines)
                
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
    # Format the chunks with metadata
    result = []
    for i, c_text in enumerate(chunks):
        # We prepend the heading to the chunk text so the embedding model has context
        full_text = f"{section.number} {section.title}\n\n{c_text}"
        
        metadata = {
            "chunk_id": generate_chunk_id(section.spec, section.version, section.number, i),
            "spec": section.spec,
            "version": section.version,
            "section": section.number,
            "title": section.title,
            "parent": section.parent or "",
            "text": full_text
        }
        result.append(metadata)
        
    return result
