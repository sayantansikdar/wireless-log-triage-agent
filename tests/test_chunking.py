from core.ingest.parse_3gpp import parse_markdown_to_sections
from core.ingest.chunking import chunk_section
from core.ingest.cause_codes import extract_cause_codes_from_markdown

def test_parse_markdown():
    md = """# 5.5.1 Title
Some front matter.
## 5.5.1.2 Subtitle
More text.
# 6.0 Next Chapter
Text."""
    
    sections = parse_markdown_to_sections(md, spec="24.301", version="18.3.0")
    
    assert len(sections) == 3
    assert sections[0].number == "5.5.1"
    assert sections[0].level == 1
    assert "Some front matter." in sections[0].content
    assert sections[0].parent is None
    
    assert sections[1].number == "5.5.1.2"
    assert sections[1].level == 2
    assert "More text." in sections[1].content
    assert sections[1].parent == "5.5.1"
    
    assert sections[2].number == "6.0"
    assert sections[2].level == 1

def test_chunking_preserves_metadata():
    md = """## 5.5.1.2.5 Attach not accepted by the network
If the attach request cannot be accepted by the network..."""
    sections = parse_markdown_to_sections(md, spec="24.301", version="18.3.0")
    
    chunks = chunk_section(sections[0], max_chars=2000)
    assert len(chunks) == 1
    assert chunks[0]["spec"] == "24.301"
    assert chunks[0]["section"] == "5.5.1.2.5"
    assert "Attach not accepted" in chunks[0]["text"]
    assert "If the attach request" in chunks[0]["text"]

def test_cause_code_extraction():
    md = """
Some text.
| Cause value | Description |
|---|---|
| 3 | Illegal MS |
| 15 | No Suitable Cells In tracking area |
    """
    
    codes = extract_cause_codes_from_markdown(md)
    assert "3" in codes
    assert "#3" in codes
    assert codes["3"] == "Illegal MS"
    assert codes["#15"] == "No Suitable Cells In tracking area"
