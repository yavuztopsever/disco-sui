import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.manipulation.manipulator import Manipulator

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def manipulator(mock_context, mock_processor):
    return Manipulator(
        context=mock_context,
        processor=mock_processor
    )

def test_manipulator_initialization(manipulator):
    """Test manipulator initialization."""
    assert manipulator is not None
    assert manipulator.processor is not None

def test_add_frontmatter(manipulator, mock_processor):
    """Test adding frontmatter to content."""
    content = "# Test Content"
    metadata = {
        "title": "Test Note",
        "tags": ["test", "example"]
    }
    mock_processor.add_frontmatter.return_value = {
        "success": True,
        "content": """---
title: Test Note
tags: [test, example]
---
# Test Content"""
    }
    
    result = manipulator.add_frontmatter(content, metadata)
    assert result["success"] is True
    assert "content" in result
    assert "title:" in result["content"]

def test_remove_frontmatter(manipulator, mock_processor):
    """Test removing frontmatter from content."""
    content = """---
title: Test Note
tags: [test]
---
# Test Content"""
    mock_processor.remove_frontmatter.return_value = {
        "success": True,
        "content": "# Test Content",
        "metadata": {
            "title": "Test Note",
            "tags": ["test"]
        }
    }
    
    result = manipulator.remove_frontmatter(content)
    assert result["success"] is True
    assert "content" in result
    assert "metadata" in result

def test_update_frontmatter(manipulator, mock_processor):
    """Test updating frontmatter in content."""
    content = """---
title: Old Title
tags: [old]
---
# Content"""
    updates = {
        "title": "New Title",
        "tags": ["new", "updated"]
    }
    mock_processor.update_frontmatter.return_value = {
        "success": True,
        "content": """---
title: New Title
tags: [new, updated]
---
# Content"""
    }
    
    result = manipulator.update_frontmatter(content, updates)
    assert result["success"] is True
    assert "New Title" in result["content"]

def test_add_tags(manipulator, mock_processor):
    """Test adding tags to content."""
    content = """---
title: Test
tags: [existing]
---
# Content"""
    new_tags = ["new", "tags"]
    mock_processor.add_tags.return_value = {
        "success": True,
        "content": """---
title: Test
tags: [existing, new, tags]
---
# Content"""
    }
    
    result = manipulator.add_tags(content, new_tags)
    assert result["success"] is True
    assert all(tag in result["content"] for tag in new_tags)

def test_remove_tags(manipulator, mock_processor):
    """Test removing tags from content."""
    content = """---
title: Test
tags: [tag1, tag2, tag3]
---
# Content"""
    tags_to_remove = ["tag1", "tag3"]
    mock_processor.remove_tags.return_value = {
        "success": True,
        "content": """---
title: Test
tags: [tag2]
---
# Content"""
    }
    
    result = manipulator.remove_tags(content, tags_to_remove)
    assert result["success"] is True
    assert all(tag not in result["content"] for tag in tags_to_remove)

def test_add_links(manipulator, mock_processor):
    """Test adding links to content."""
    content = "# Test Content"
    links = [
        {"text": "Link 1", "target": "note1.md"},
        {"text": "Link 2", "target": "note2.md"}
    ]
    mock_processor.add_links.return_value = {
        "success": True,
        "content": """# Test Content
[[note1.md|Link 1]]
[[note2.md|Link 2]]"""
    }
    
    result = manipulator.add_links(content, links)
    assert result["success"] is True
    assert all(link["text"] in result["content"] for link in links)

def test_remove_links(manipulator, mock_processor):
    """Test removing links from content."""
    content = """# Test
[[note1.md|Link 1]]
[[note2.md|Link 2]]"""
    links_to_remove = ["note1.md"]
    mock_processor.remove_links.return_value = {
        "success": True,
        "content": """# Test
[[note2.md|Link 2]]"""
    }
    
    result = manipulator.remove_links(content, links_to_remove)
    assert result["success"] is True
    assert "note1.md" not in result["content"]

def test_update_links(manipulator, mock_processor):
    """Test updating links in content."""
    content = """# Test
[[old_note.md|Old Link]]"""
    old_link = "old_note.md"
    new_link = "new_note.md"
    mock_processor.update_links.return_value = {
        "success": True,
        "content": """# Test
[[new_note.md|Old Link]]"""
    }
    
    result = manipulator.update_links(content, old_link, new_link)
    assert result["success"] is True
    assert new_link in result["content"]
    assert old_link not in result["content"]

def test_format_content(manipulator, mock_processor):
    """Test content formatting."""
    content = "# Test\n\n\nExtra spaces\n  Indented"
    mock_processor.format_content.return_value = {
        "success": True,
        "content": "# Test\n\nExtra spaces\nIndented"
    }
    
    result = manipulator.format_content(content)
    assert result["success"] is True
    assert result["content"].count("\n\n") == 1

def test_extract_sections(manipulator, mock_processor):
    """Test extracting sections from content."""
    content = """# Title
## Section 1
Content 1
## Section 2
Content 2"""
    mock_processor.extract_sections.return_value = {
        "success": True,
        "sections": [
            {"level": 1, "title": "Title", "content": "# Title"},
            {"level": 2, "title": "Section 1", "content": "## Section 1\nContent 1"},
            {"level": 2, "title": "Section 2", "content": "## Section 2\nContent 2"}
        ]
    }
    
    result = manipulator.extract_sections(content)
    assert result["success"] is True
    assert len(result["sections"]) == 3

def test_update_section(manipulator, mock_processor):
    """Test updating a section in content."""
    content = """# Title
## Section 1
Old content
## Section 2
Content 2"""
    section_title = "Section 1"
    new_content = "New content"
    mock_processor.update_section.return_value = {
        "success": True,
        "content": """# Title
## Section 1
New content
## Section 2
Content 2"""
    }
    
    result = manipulator.update_section(content, section_title, new_content)
    assert result["success"] is True
    assert new_content in result["content"]

def test_merge_content(manipulator, mock_processor):
    """Test merging content from multiple sources."""
    contents = [
        "# Part 1\nContent 1",
        "# Part 2\nContent 2"
    ]
    mock_processor.merge_content.return_value = {
        "success": True,
        "content": """# Part 1
Content 1
# Part 2
Content 2"""
    }
    
    result = manipulator.merge_content(contents)
    assert result["success"] is True
    assert "Part 1" in result["content"]
    assert "Part 2" in result["content"]

def test_split_content(manipulator, mock_processor):
    """Test splitting content into multiple parts."""
    content = """# Part 1
Content 1
# Part 2
Content 2"""
    mock_processor.split_content.return_value = {
        "success": True,
        "parts": [
            "# Part 1\nContent 1",
            "# Part 2\nContent 2"
        ]
    }
    
    result = manipulator.split_content(content)
    assert result["success"] is True
    assert len(result["parts"]) == 2

def test_error_handling(manipulator, mock_processor):
    """Test error handling."""
    mock_processor.add_frontmatter.side_effect = Exception("Test error")
    
    result = manipulator.add_frontmatter("content", {})
    assert result["success"] is False
    assert "error" in result

def test_validate_content(manipulator, mock_processor):
    """Test content validation."""
    content = "# Valid Content"
    mock_processor.validate_content.return_value = {
        "success": True,
        "valid": True,
        "issues": []
    }
    
    result = manipulator.validate_content(content)
    assert result["success"] is True
    assert result["valid"] is True 