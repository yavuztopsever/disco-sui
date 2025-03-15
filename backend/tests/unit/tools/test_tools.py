"""Unit tests for tool implementations."""
import pytest
from pathlib import Path
from typing import Dict, Any

@pytest.mark.unit
class TestNoteTool:
    """Test suite for note manipulation tools."""
    
    def test_note_creation(self, mock_context, mock_fs, test_data_generator,
                          assertion_helper):
        """Test note creation functionality."""
        from src.tools.note_tools import NoteTool
        
        note_tool = NoteTool(context=mock_context)
        
        # Create note with basic content
        test_note = test_data_generator("note")
        result = note_tool.create_note(
            title=test_note["title"],
            content=test_note["content"]
        )
        assertion_helper["assert_success"](result)
        assert result["file_path"].endswith(".md")
        
        # Create note with template
        result = note_tool.create_note(
            title="Template Note",
            content="Content",
            template="basic.md"
        )
        assertion_helper["assert_success"](result)
        assert "yaml" in result["content"].lower()
    
    def test_note_modification(self, mock_context, mock_fs, test_data_generator,
                             assertion_helper):
        """Test note modification operations."""
        from src.tools.note_tools import NoteTool
        
        note_tool = NoteTool(context=mock_context)
        test_note = test_data_generator("note")
        
        # Update note content
        result = note_tool.update_note(
            file_path="test.md",
            content="Updated content"
        )
        assertion_helper["assert_success"](result)
        
        # Add metadata
        result = note_tool.add_metadata(
            file_path="test.md",
            metadata={"tags": ["test"]}
        )
        assertion_helper["assert_success"](result)
        assert "tags" in result["metadata"]

@pytest.mark.unit
class TestSearchTool:
    """Test suite for search tools."""
    
    def test_content_search(self, mock_context, mock_fs, assertion_helper):
        """Test content search functionality."""
        from src.tools.search_tools import SearchTool
        
        search_tool = SearchTool(context=mock_context)
        
        # Search by text
        result = search_tool.search_content("test query")
        assertion_helper["assert_success"](result)
        assert isinstance(result["matches"], list)
        
        # Search with filters
        result = search_tool.search_content(
            "test query",
            file_type="md",
            max_results=5
        )
        assertion_helper["assert_success"](result)
        assert len(result["matches"]) <= 5
    
    def test_semantic_search(self, mock_context, mock_fs, assertion_helper):
        """Test semantic search functionality."""
        from src.tools.search_tools import SearchTool
        
        search_tool = SearchTool(context=mock_context)
        
        # Semantic similarity search
        result = search_tool.semantic_search(
            query="concept similar to test",
            threshold=0.5
        )
        assertion_helper["assert_success"](result)
        assert "similarity_scores" in result

@pytest.mark.unit
class TestTagTool:
    """Test suite for tag management tools."""
    
    def test_tag_operations(self, mock_context, mock_fs, assertion_helper):
        """Test tag manipulation operations."""
        from src.tools.tag_tools import TagTool
        
        tag_tool = TagTool(context=mock_context)
        
        # Add tags
        result = tag_tool.add_tags(
            file_path="test.md",
            tags=["test", "example"]
        )
        assertion_helper["assert_success"](result)
        assert len(result["added_tags"]) == 2
        
        # Remove tags
        result = tag_tool.remove_tags(
            file_path="test.md",
            tags=["example"]
        )
        assertion_helper["assert_success"](result)
        assert len(result["removed_tags"]) == 1
    
    def test_tag_analysis(self, mock_context, mock_fs, assertion_helper):
        """Test tag analysis functionality."""
        from src.tools.tag_tools import TagTool
        
        tag_tool = TagTool(context=mock_context)
        
        # Analyze tag usage
        result = tag_tool.analyze_tags()
        assertion_helper["assert_success"](result)
        assert "tag_counts" in result
        assert "tag_relationships" in result

@pytest.mark.unit
class TestLinkTool:
    """Test suite for link management tools."""
    
    def test_link_operations(self, mock_context, mock_fs, assertion_helper):
        """Test link manipulation operations."""
        from src.tools.link_tools import LinkTool
        
        link_tool = LinkTool(context=mock_context)
        
        # Create link
        result = link_tool.create_link(
            source="source.md",
            target="target.md",
            link_text="Link"
        )
        assertion_helper["assert_success"](result)
        assert "[[" in result["link"]
        
        # Update link
        result = link_tool.update_link(
            file_path="test.md",
            old_target="old.md",
            new_target="new.md"
        )
        assertion_helper["assert_success"](result)
        assert result["updated_count"] > 0
    
    def test_link_analysis(self, mock_context, mock_fs, assertion_helper):
        """Test link analysis functionality."""
        from src.tools.link_tools import LinkTool
        
        link_tool = LinkTool(context=mock_context)
        
        # Analyze links
        result = link_tool.analyze_links("test.md")
        assertion_helper["assert_success"](result)
        assert "valid_links" in result
        assert "broken_links" in result
        
        # Generate link graph
        result = link_tool.generate_link_graph()
        assertion_helper["assert_success"](result)
        assert "nodes" in result
        assert "edges" in result 