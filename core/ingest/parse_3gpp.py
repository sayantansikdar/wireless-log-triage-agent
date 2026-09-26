import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Section:
    level: int
    number: str
    title: str
    content: str
    parent: Optional[str] = None
    spec: str = ""
    version: str = ""

def parse_markdown_to_sections(md_text: str, spec: str, version: str) -> List[Section]:
    """
    Parses a Markdown string into a hierarchy of sections.
    Relies on ATX headings (e.g., `# 5.5.1 Title`).
    """
    sections = []
    # Match ATX headings. Group 1: hashes, Group 2: section number, Group 3: title
    heading_pattern = re.compile(r'^(#{1,6})\s+([\d\.]+)\s+(.*)$', re.MULTILINE)
    
    # Split text by heading
    matches = list(heading_pattern.finditer(md_text))
    
    if not matches:
        # No headings found, return single chunk
        return [Section(level=0, number="", title="", content=md_text.strip(), spec=spec, version=version)]
        
    # Text before first heading (front matter)
    front_matter = md_text[:matches[0].start()].strip()
    if front_matter:
        sections.append(Section(level=0, number="", title="Front Matter", content=front_matter, spec=spec, version=version))
        
    active_hierarchy = {} # level -> section_number
    
    for i, match in enumerate(matches):
        level = len(match.group(1))
        number = match.group(2).strip('. ') # strip trailing dots
        title = match.group(3).strip()
        
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(md_text)
        content = md_text[start_idx:end_idx].strip()
        
        # Determine parent
        parent = None
        for l in range(level - 1, 0, -1):
            if l in active_hierarchy:
                parent = active_hierarchy[l]
                break
                
        active_hierarchy[level] = number
        # Clear deeper levels
        for l in list(active_hierarchy.keys()):
            if l > level:
                del active_hierarchy[l]
                
        sections.append(Section(
            level=level,
            number=number,
            title=title,
            content=content,
            parent=parent,
            spec=spec,
            version=version
        ))
        
    return sections
