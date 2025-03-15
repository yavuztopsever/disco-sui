import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.processor import ContentProcessor

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def content_processor(mock_context):
    return ContentProcessor(context=mock_context)

def test_processor_initialization(content_processor):
    """Test processor initialization."""
    assert content_processor is not None
    assert content_processor.context is not None

def test_process_markdown(content_processor):
    """Test markdown processing."""
    content = """# Test Title
This is a **bold** text with *italics*."""
    
    result = content_processor.process_markdown(content)
    assert result["success"] is True
    assert "<h1>" in result["html"]
    assert "<strong>" in result["html"]
    assert "<em>" in result["html"]

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
    content = """# Links
[[internal_note|Internal Link]]
[External Link](https://example.com)
[[another_note]]"""
    
    result = content_processor.process_links(content)
    assert result["success"] is True
    assert len(result["internal_links"]) == 2
    assert len(result["external_links"]) == 1

def test_validate_content(content_processor):
    """Test content validation."""
    valid_content = """---
title: Valid Note
---
# Valid Content
Valid markdown content."""
    
    result = content_processor.validate_content(valid_content)
    assert result["success"] is True
    assert result["valid"] is True
    assert len(result["issues"]) == 0

def test_process_tags(content_processor):
    """Test tag processing."""
    content = """---
tags: [frontmatter_tag1, frontmatter_tag2]
---
# Content
#inline_tag1 #inline_tag2"""
    
    result = content_processor.process_tags(content)
    assert result["success"] is True
    assert len(result["frontmatter_tags"]) == 2
    assert len(result["inline_tags"]) == 2

def test_analyze_structure(content_processor):
    """Test content structure analysis."""
    content = """# Title
## Section 1
Content
### Subsection 1.1
Content
## Section 2
Content"""
    
    result = content_processor.analyze_structure(content)
    assert result["success"] is True
    assert result["depth"] == 3
    assert len(result["sections"]) == 4

def test_process_code_blocks(content_processor):
    """Test code block processing."""
    content = """# Code Examples
```python
def test():
    pass
```
```javascript
function test() {
    return true;
}
```"""
    
    result = content_processor.process_code_blocks(content)
    assert result["success"] is True
    assert len(result["code_blocks"]) == 2
    assert "python" in result["languages"]
    assert "javascript" in result["languages"]

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
    assert result["tables"][0]["headers"] == ["Header 1", "Header 2"]
    assert len(result["tables"][0]["rows"]) == 2

def test_process_images(content_processor):
    """Test image processing."""
    content = """# Images
![Local Image](assets/image.png)
![External Image](https://example.com/image.jpg)"""
    
    result = content_processor.process_images(content)
    assert result["success"] is True
    assert len(result["local_images"]) == 1
    assert len(result["external_images"]) == 1

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
This is a citation [@author2024].
Multiple citations [@author2024; @another2023]."""
    
    result = content_processor.process_citations(content)
    assert result["success"] is True
    assert len(result["citations"]) == 3

def test_process_footnotes(content_processor):
    """Test footnote processing."""
    content = """# Footnotes
Text with a footnote[^1].
Another footnote[^2].

[^1]: First footnote content
[^2]: Second footnote content"""
    
    result = content_processor.process_footnotes(content)
    assert result["success"] is True
    assert len(result["footnotes"]) == 2

def test_error_handling_invalid_content(content_processor):
    """Test error handling for invalid content."""
    invalid_content = None
    
    result = content_processor.process_markdown(invalid_content)
    assert result["success"] is False
    assert "error" in result

def test_error_handling_invalid_frontmatter(content_processor):
    """Test error handling for invalid frontmatter."""
    invalid_frontmatter = """---
invalid: yaml: [
---
# Content"""
    
    result = content_processor.extract_metadata(invalid_frontmatter)
    assert result["success"] is False
    assert "error" in result

def test_batch_processing(content_processor):
    """Test batch content processing."""
    contents = [
        "# Document 1\nContent 1",
        "# Document 2\nContent 2"
    ]
    
    result = content_processor.batch_process(contents)
    assert result["success"] is True
    assert len(result["results"]) == 2
    assert all(r["success"] for r in result["results"])

def test_process_template(content_processor):
    """Test template processing."""
    template = """# {{title}}
Date: {{date}}
Author: {{author}}"""
    variables = {
        "title": "Test Note",
        "date": "2024-01-01",
        "author": "Test Author"
    }
    
    result = content_processor.process_template(template, variables)
    assert result["success"] is True
    assert variables["title"] in result["content"]
    assert variables["date"] in result["content"]
    assert variables["author"] in result["content"] 