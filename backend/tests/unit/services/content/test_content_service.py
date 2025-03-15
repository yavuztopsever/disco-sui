import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.content_service import ContentService

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def mock_manipulator():
    return MagicMock()

@pytest.fixture
def content_service(mock_context, mock_processor, mock_manipulator):
    return ContentService(
        context=mock_context,
        processor=mock_processor,
        manipulator=mock_manipulator
    )

def test_service_initialization(content_service):
    """Test service initialization."""
    assert content_service is not None
    assert content_service.processor is not None
    assert content_service.manipulator is not None

def test_process_content(content_service, mock_processor):
    """Test content processing."""
    content = "# Test Content"
    mock_processor.process_markdown.return_value = {
        "success": True,
        "html": "<h1>Test Content</h1>",
        "metadata": {}
    }
    
    result = content_service.process_content(content)
    assert result["success"] is True
    assert "html" in result
    assert "<h1>" in result["html"]

def test_extract_metadata(content_service, mock_processor):
    """Test metadata extraction."""
    content = """---
title: Test Note
tags: [test]
---
# Content"""
    mock_processor.extract_metadata.return_value = {
        "success": True,
        "metadata": {
            "title": "Test Note",
            "tags": ["test"]
        }
    }
    
    result = content_service.extract_metadata(content)
    assert result["success"] is True
    assert result["metadata"]["title"] == "Test Note"
    assert "test" in result["metadata"]["tags"]

def test_update_metadata(content_service, mock_manipulator):
    """Test metadata updating."""
    content = """---
title: Old Title
---
# Content"""
    updates = {
        "title": "New Title",
        "tags": ["new"]
    }
    mock_manipulator.update_frontmatter.return_value = {
        "success": True,
        "content": """---
title: New Title
tags: [new]
---
# Content"""
    }
    
    result = content_service.update_metadata(content, updates)
    assert result["success"] is True
    assert "New Title" in result["content"]

def test_add_tags(content_service, mock_manipulator):
    """Test adding tags."""
    content = "# Content"
    tags = ["tag1", "tag2"]
    mock_manipulator.add_tags.return_value = {
        "success": True,
        "content": """---
tags: [tag1, tag2]
---
# Content"""
    }
    
    result = content_service.add_tags(content, tags)
    assert result["success"] is True
    assert all(tag in result["content"] for tag in tags)

def test_remove_tags(content_service, mock_manipulator):
    """Test removing tags."""
    content = """---
tags: [tag1, tag2, tag3]
---
# Content"""
    tags = ["tag1", "tag3"]
    mock_manipulator.remove_tags.return_value = {
        "success": True,
        "content": """---
tags: [tag2]
---
# Content"""
    }
    
    result = content_service.remove_tags(content, tags)
    assert result["success"] is True
    assert all(tag not in result["content"] for tag in tags)

def test_process_links(content_service, mock_processor):
    """Test link processing."""
    content = """# Links
[[note1|Link 1]]
[External](https://example.com)"""
    mock_processor.process_links.return_value = {
        "success": True,
        "internal_links": [{"text": "Link 1", "target": "note1"}],
        "external_links": [{"text": "External", "url": "https://example.com"}]
    }
    
    result = content_service.process_links(content)
    assert result["success"] is True
    assert len(result["internal_links"]) == 1
    assert len(result["external_links"]) == 1

def test_update_links(content_service, mock_manipulator):
    """Test updating links."""
    content = "[[old_note|Link]]"
    old_link = "old_note"
    new_link = "new_note"
    mock_manipulator.update_links.return_value = {
        "success": True,
        "content": "[[new_note|Link]]"
    }
    
    result = content_service.update_links(content, old_link, new_link)
    assert result["success"] is True
    assert new_link in result["content"]
    assert old_link not in result["content"]

def test_format_content(content_service, mock_manipulator):
    """Test content formatting."""
    content = "# Title\n\n\nExtra spaces"
    mock_manipulator.format_content.return_value = {
        "success": True,
        "content": "# Title\n\nExtra spaces"
    }
    
    result = content_service.format_content(content)
    assert result["success"] is True
    assert result["content"].count("\n\n") == 1

def test_validate_content(content_service, mock_processor):
    """Test content validation."""
    content = "# Valid Content"
    mock_processor.validate_content.return_value = {
        "success": True,
        "valid": True,
        "issues": []
    }
    
    result = content_service.validate_content(content)
    assert result["success"] is True
    assert result["valid"] is True

def test_analyze_structure(content_service, mock_processor):
    """Test structure analysis."""
    content = """# Title
## Section 1
### Subsection"""
    mock_processor.analyze_structure.return_value = {
        "success": True,
        "depth": 3,
        "sections": [
            {"level": 1, "title": "Title"},
            {"level": 2, "title": "Section 1"},
            {"level": 3, "title": "Subsection"}
        ]
    }
    
    result = content_service.analyze_structure(content)
    assert result["success"] is True
    assert result["depth"] == 3
    assert len(result["sections"]) == 3

def test_process_templates(content_service, mock_processor):
    """Test template processing."""
    template = "# {{title}}"
    variables = {"title": "Test"}
    mock_processor.process_template.return_value = {
        "success": True,
        "content": "# Test"
    }
    
    result = content_service.process_template(template, variables)
    assert result["success"] is True
    assert "# Test" in result["content"]

def test_batch_processing(content_service, mock_processor):
    """Test batch content processing."""
    contents = ["# Doc 1", "# Doc 2"]
    mock_processor.batch_process.return_value = {
        "success": True,
        "results": [
            {"success": True, "html": "<h1>Doc 1</h1>"},
            {"success": True, "html": "<h1>Doc 2</h1>"}
        ]
    }
    
    result = content_service.batch_process(contents)
    assert result["success"] is True
    assert len(result["results"]) == 2

def test_error_handling(content_service, mock_processor):
    """Test error handling."""
    mock_processor.process_markdown.side_effect = Exception("Test error")
    
    result = content_service.process_content("# Test")
    assert result["success"] is False
    assert "error" in result

def test_merge_content(content_service, mock_manipulator):
    """Test content merging."""
    contents = ["# Part 1", "# Part 2"]
    mock_manipulator.merge_content.return_value = {
        "success": True,
        "content": "# Part 1\n# Part 2"
    }
    
    result = content_service.merge_content(contents)
    assert result["success"] is True
    assert "Part 1" in result["content"]
    assert "Part 2" in result["content"]

def test_split_content(content_service, mock_manipulator):
    """Test content splitting."""
    content = "# Part 1\n# Part 2"
    mock_manipulator.split_content.return_value = {
        "success": True,
        "parts": ["# Part 1", "# Part 2"]
    }
    
    result = content_service.split_content(content)
    assert result["success"] is True
    assert len(result["parts"]) == 2 