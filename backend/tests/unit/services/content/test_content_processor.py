import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.processor import ContentProcessor

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_manipulator():
    return MagicMock()

@pytest.fixture
def content_processor(mock_context, mock_manipulator):
    return ContentProcessor(
        context=mock_context,
        manipulator=mock_manipulator
    )

def test_content_processor_initialization(content_processor):
    """Test content processor initialization."""
    assert content_processor is not None
    assert content_processor.manipulator is not None

def test_process_markdown(content_processor):
    """Test markdown processing."""
    content = """# Title
## Section
- List item 1
- List item 2
"""
    
    result = content_processor.process_markdown(content)
    assert result["success"] is True
    assert "html" in result
    assert "<h1>Title</h1>" in result["html"]
    assert "<ul>" in result["html"]

def test_extract_metadata(content_processor):
    """Test metadata extraction."""
    content = """---
title: Test Note
tags: [test, example]
date: 2024-01-01
---
# Content"""
    
    result = content_processor.extract_metadata(content)
    assert result["success"] is True
    assert result["metadata"]["title"] == "Test Note"
    assert "test" in result["metadata"]["tags"]
    assert result["metadata"]["date"] == "2024-01-01"

def test_process_links(content_processor):
    """Test link processing."""
    content = """# Test
[[note1.md|Link 1]]
[[note2.md|Link 2]]
[External](https://example.com)"""
    
    result = content_processor.process_links(content)
    assert result["success"] is True
    assert len(result["internal_links"]) == 2
    assert len(result["external_links"]) == 1
    assert "note1.md" in [link["target"] for link in result["internal_links"]]

def test_validate_content(content_processor):
    """Test content validation."""
    valid_content = """---
title: Valid Note
---
# Valid Content
## Section"""
    
    result = content_processor.validate_content(valid_content)
    assert result["success"] is True
    assert result["valid"] is True
    assert len(result["issues"]) == 0

def test_process_tags(content_processor):
    """Test tag processing."""
    content = """---
tags: [project, todo, important]
---
#status/active #type/note"""
    
    result = content_processor.process_tags(content)
    assert result["success"] is True
    assert len(result["frontmatter_tags"]) == 3
    assert len(result["inline_tags"]) == 2
    assert "project" in result["frontmatter_tags"]
    assert "status/active" in result["inline_tags"]

def test_analyze_structure(content_processor):
    """Test content structure analysis."""
    content = """# Main Title
## Section 1
Content
### Subsection 1.1
Content
## Section 2
Content"""
    
    result = content_processor.analyze_structure(content)
    assert result["success"] is True
    assert result["structure"]["depth"] == 3
    assert len(result["structure"]["sections"]) == 4

def test_process_code_blocks(content_processor):
    """Test code block processing."""
    content = """# Code Example
```python
def test():
    return "Hello"
```
```javascript
console.log("Test");
```"""
    
    result = content_processor.process_code_blocks(content)
    assert result["success"] is True
    assert len(result["code_blocks"]) == 2
    assert "python" in [block["language"] for block in result["code_blocks"]]

def test_process_tables(content_processor):
    """Test table processing."""
    content = """# Tables
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""
    
    result = content_processor.process_tables(content)
    assert result["success"] is True
    assert len(result["tables"]) == 1
    assert len(result["tables"][0]["headers"]) == 2
    assert len(result["tables"][0]["rows"]) == 2

def test_process_images(content_processor):
    """Test image processing."""
    content = """# Images
![Image 1](image1.png)
![Image 2](https://example.com/image2.jpg)"""
    
    result = content_processor.process_images(content)
    assert result["success"] is True
    assert len(result["images"]) == 2
    assert any(img["is_local"] for img in result["images"])
    assert any(not img["is_local"] for img in result["images"])

def test_error_handling_invalid_content(content_processor):
    """Test error handling for invalid content."""
    invalid_content = None
    
    result = content_processor.process_markdown(invalid_content)
    assert result["success"] is False
    assert "error" in result

def test_process_math(content_processor):
    """Test math expression processing."""
    content = """# Math
Inline math: $E = mc^2$
Block math:
$$
F = ma
$$"""
    
    result = content_processor.process_math(content)
    assert result["success"] is True
    assert len(result["inline_math"]) == 1
    assert len(result["block_math"]) == 1

def test_process_citations(content_processor):
    """Test citation processing."""
    content = """# Citations
As mentioned in [@reference1]
Multiple citations [@ref1; @ref2]"""
    
    result = content_processor.process_citations(content)
    assert result["success"] is True
    assert len(result["citations"]) == 3
    assert "reference1" in [cite["key"] for cite in result["citations"]]

def test_process_footnotes(content_processor):
    """Test footnote processing."""
    content = """# Footnotes
Text with a footnote[^1]
More text[^note]

[^1]: First footnote
[^note]: Second footnote"""
    
    result = content_processor.process_footnotes(content)
    assert result["success"] is True
    assert len(result["footnotes"]) == 2
    assert "1" in result["footnotes"]
    assert "note" in result["footnotes"]

def test_batch_processing(content_processor):
    """Test batch content processing."""
    contents = [
        "# Document 1\nContent",
        "# Document 2\nContent"
    ]
    
    result = content_processor.batch_process(contents)
    assert result["success"] is True
    assert len(result["results"]) == 2
    assert all(res["success"] for res in result["results"]) 