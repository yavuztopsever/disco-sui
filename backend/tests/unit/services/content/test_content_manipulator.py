import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.content_manipulator import ContentManipulator

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def content_manipulator(mock_context, mock_processor):
    return ContentManipulator(
        context=mock_context,
        processor=mock_processor
    )

def test_content_manipulator_initialization(content_manipulator):
    """Test content manipulator initialization."""
    assert content_manipulator is not None
    assert content_manipulator.processor is not None

def test_add_frontmatter(content_manipulator):
    """Test adding frontmatter to content."""
    content = "# Test Content"
    metadata = {
        "title": "Test Note",
        "tags": ["test", "example"],
        "date": "2024-01-01"
    }
    
    result = content_manipulator.add_frontmatter(content, metadata)
    assert result["success"] is True
    assert "---" in result["content"]
    assert "title: Test Note" in result["content"]
    assert "tags: [test, example]" in result["content"]
    assert content in result["content"]

def test_remove_frontmatter(content_manipulator):
    """Test removing frontmatter from content."""
    content = """---
title: Test Note
tags: [test]
---
# Test Content"""
    
    result = content_manipulator.remove_frontmatter(content)
    assert result["success"] is True
    assert "---" not in result["content"]
    assert "# Test Content" in result["content"]

def test_update_frontmatter(content_manipulator):
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
    
    result = content_manipulator.update_frontmatter(content, updates)
    assert result["success"] is True
    assert "New Title" in result["content"]
    assert "new" in result["content"]
    assert "updated" in result["content"]

def test_add_tags(content_manipulator):
    """Test adding tags to content."""
    content = """---
title: Test
tags: [existing]
---
# Content"""
    new_tags = ["new", "test"]
    
    result = content_manipulator.add_tags(content, new_tags)
    assert result["success"] is True
    assert all(tag in result["content"] for tag in new_tags)

def test_remove_tags(content_manipulator):
    """Test removing tags from content."""
    content = """---
title: Test
tags: [tag1, tag2, tag3]
---
# Content"""
    tags_to_remove = ["tag1", "tag3"]
    
    result = content_manipulator.remove_tags(content, tags_to_remove)
    assert result["success"] is True
    assert "tag2" in result["content"]
    assert all(tag not in result["content"] for tag in tags_to_remove)

def test_add_links(content_manipulator):
    """Test adding links to content."""
    content = "# Test Content"
    links = [
        {"text": "Link 1", "url": "note1.md"},
        {"text": "Link 2", "url": "note2.md"}
    ]
    
    result = content_manipulator.add_links(content, links)
    assert result["success"] is True
    assert "[[note1.md|Link 1]]" in result["content"]
    assert "[[note2.md|Link 2]]" in result["content"]

def test_remove_links(content_manipulator):
    """Test removing links from content."""
    content = "# Test\n[[note1.md|Link 1]]\nText\n[[note2.md|Link 2]]"
    links_to_remove = ["note1.md"]
    
    result = content_manipulator.remove_links(content, links_to_remove)
    assert result["success"] is True
    assert "[[note1.md" not in result["content"]
    assert "[[note2.md" in result["content"]

def test_update_links(content_manipulator):
    """Test updating links in content."""
    content = "# Test\n[[old_note.md|Link]]\nText"
    link_updates = {
        "old_note.md": "new_note.md"
    }
    
    result = content_manipulator.update_links(content, link_updates)
    assert result["success"] is True
    assert "[[new_note.md" in result["content"]
    assert "old_note.md" not in result["content"]

def test_format_content(content_manipulator):
    """Test content formatting."""
    content = "# Test\n\n\nExtra spaces\n  Indented"
    
    result = content_manipulator.format_content(content)
    assert result["success"] is True
    assert "\n\n\n" not in result["content"]
    assert result["content"].startswith("# Test")

def test_extract_sections(content_manipulator):
    """Test extracting sections from content."""
    content = """# Main Title
Content
## Section 1
Content 1
## Section 2
Content 2"""
    
    result = content_manipulator.extract_sections(content)
    assert result["success"] is True
    assert len(result["sections"]) == 3
    assert result["sections"][0]["level"] == 1
    assert result["sections"][1]["level"] == 2

def test_update_section(content_manipulator):
    """Test updating a section in content."""
    content = """# Main Title
Content
## Section 1
Old content
## Section 2
Content 2"""
    section_update = {
        "title": "Section 1",
        "content": "New content"
    }
    
    result = content_manipulator.update_section(content, section_update)
    assert result["success"] is True
    assert "New content" in result["content"]
    assert "Old content" not in result["content"]

def test_error_handling(content_manipulator):
    """Test error handling for invalid content."""
    invalid_content = None
    
    result = content_manipulator.format_content(invalid_content)
    assert result["success"] is False
    assert "error" in result

def test_merge_content(content_manipulator):
    """Test merging content from multiple sources."""
    contents = [
        "# Part 1\nContent 1",
        "# Part 2\nContent 2"
    ]
    
    result = content_manipulator.merge_content(contents)
    assert result["success"] is True
    assert "Part 1" in result["content"]
    assert "Part 2" in result["content"]

def test_split_content(content_manipulator):
    """Test splitting content into multiple parts."""
    content = """# Part 1
Content 1
# Part 2
Content 2"""
    
    result = content_manipulator.split_content(content)
    assert result["success"] is True
    assert len(result["parts"]) == 2
    assert "Part 1" in result["parts"][0]
    assert "Part 2" in result["parts"][1] 