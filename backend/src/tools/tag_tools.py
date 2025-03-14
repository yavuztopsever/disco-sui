from typing import Dict, Any, Optional, List
from .base_tools import BaseTool, FrontmatterManagerTool
from ..features.tag_management.tag_manager import TagManager
from ..features.tag_management.tag_validator import TagValidator
import re
from smolagents import Tool

class TagManagerTool(BaseTool):
    name = "tag_manager"
    description = "Comprehensive tag management for Obsidian notes"
    inputs = {
        "action": {
            "type": "string",
            "description": "The action to perform",
            "enum": ["add", "remove", "list", "search", "get_note_tags", "get_related", "suggest", "get_stats"]
        },
        "path": {
            "type": "string",
            "description": "The path to the note (required for add, remove, get_note_tags)",
            "nullable": True
        },
        "tag": {
            "type": "string",
            "description": "The tag to add/remove/search (required for add, remove, search, get_related)",
            "nullable": True
        },
        "tag_type": {
            "type": "string",
            "description": "The type of tag (concept, place, brand, company, service)",
            "nullable": True
        },
        "max_suggestions": {
            "type": "integer",
            "description": "Maximum number of tag suggestions to return",
            "default": 5,
            "nullable": True
        }
    }
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path
        self.frontmatter_manager = FrontmatterManagerTool()
        self.tag_validator = TagValidator()
        self.tag_manager = TagManager(vault_path)

    def forward(self, action: str, **kwargs) -> Dict[str, Any]:
        try:
            if action == "add":
                if not kwargs.get("path") or not kwargs.get("tag"):
                    raise ValueError("Path and tag are required for add action")
                return self.add_tag(kwargs["path"], kwargs["tag"], kwargs.get("tag_type"))
            elif action == "remove":
                if not kwargs.get("path") or not kwargs.get("tag"):
                    raise ValueError("Path and tag are required for remove action")
                return self.remove_tag(kwargs["path"], kwargs["tag"])
            elif action == "list":
                return self.list_tags()
            elif action == "search":
                if not kwargs.get("tag"):
                    raise ValueError("Tag is required for search action")
                return self.search_by_tag(kwargs["tag"])
            elif action == "get_note_tags":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for get_note_tags action")
                return self.get_note_tags(kwargs["path"])
            elif action == "get_related":
                if not kwargs.get("tag"):
                    raise ValueError("Tag is required for get_related action")
                return self.get_related_tags(kwargs["tag"])
            elif action == "suggest":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for suggest action")
                return self.suggest_tags(kwargs["path"], kwargs.get("max_suggestions", 5))
            elif action == "get_stats":
                return self.get_tag_stats()
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            return {"error": str(e)}

    def add_tag(self, path: str, tag: str, tag_type: Optional[str] = None) -> Dict[str, Any]:
        """Add a tag to a note."""
        try:
            # Validate tag
            if not self.tag_validator.validate_tag(tag):
                raise ValueError(f"Invalid tag format: {tag}")

            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.frontmatter_manager.get_frontmatter(content)
            
            if 'tags' not in frontmatter:
                frontmatter['tags'] = []
            
            if tag not in frontmatter['tags']:
                frontmatter['tags'].append(tag)
                if tag_type:
                    frontmatter[f'tag_type_{tag}'] = tag_type
            
            updated_content = self.frontmatter_manager.update_frontmatter(content, frontmatter)
            self._write_file(file_path, updated_content)
            return {"success": True, "message": f"Tag '{tag}' added to note '{path}' successfully"}
        except Exception as e:
            return {"error": str(e)}

    def remove_tag(self, path: str, tag: str) -> Dict[str, Any]:
        """Remove a tag from a note."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.frontmatter_manager.get_frontmatter(content)
            
            if 'tags' in frontmatter and tag in frontmatter['tags']:
                frontmatter['tags'].remove(tag)
                if f'tag_type_{tag}' in frontmatter:
                    del frontmatter[f'tag_type_{tag}']
                updated_content = self.frontmatter_manager.update_frontmatter(content, frontmatter)
                self._write_file(file_path, updated_content)
                return {"success": True, "message": f"Tag '{tag}' removed from note '{path}' successfully"}
            else:
                return {"error": f"Tag '{tag}' not found in note '{path}'"}
        except Exception as e:
            return {"error": str(e)}

    def list_tags(self) -> Dict[str, Any]:
        """List all tags in the vault."""
        try:
            tags_set = set()
            for file_path in self._list_files(self.vault_path):
                content = self._read_file(file_path)
                frontmatter = self.frontmatter_manager.get_frontmatter(content)
                if 'tags' in frontmatter:
                    tags_set.update(frontmatter['tags'])
            return {"success": True, "tags": list(tags_set)}
        except Exception as e:
            return {"error": str(e)}

    def get_note_tags(self, path: str) -> Dict[str, Any]:
        """Get all tags from a specific note."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.frontmatter_manager.get_frontmatter(content)
            return {"success": True, "tags": frontmatter.get('tags', [])}
        except Exception as e:
            return {"error": str(e)}

    def search_by_tag(self, tag: str) -> Dict[str, Any]:
        """Find all notes with a specific tag."""
        try:
            matching_notes = []
            for file_path in self._list_files(self.vault_path):
                content = self._read_file(file_path)
                frontmatter = self.frontmatter_manager.get_frontmatter(content)
                if 'tags' in frontmatter and tag in frontmatter['tags']:
                    matching_notes.append(file_path)
            return {"success": True, "notes": matching_notes}
        except Exception as e:
            return {"error": str(e)}

    def get_related_tags(self, tag: str) -> Dict[str, Any]:
        """Get related tags based on co-occurrence in notes."""
        try:
            related_tags = {}
            for file_path in self._list_files(self.vault_path):
                content = self._read_file(file_path)
                frontmatter = self.frontmatter_manager.get_frontmatter(content)
                if 'tags' in frontmatter and tag in frontmatter['tags']:
                    for other_tag in frontmatter['tags']:
                        if other_tag != tag:
                            related_tags[other_tag] = related_tags.get(other_tag, 0) + 1
            
            # Sort by frequency
            sorted_tags = sorted(related_tags.items(), key=lambda x: x[1], reverse=True)
            return {"success": True, "related_tags": [tag for tag, _ in sorted_tags]}
        except Exception as e:
            return {"error": str(e)}

    def suggest_tags(self, path: str, max_suggestions: int = 5) -> Dict[str, Any]:
        """Suggest relevant tags for a note based on its content."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            suggestions = self.tag_manager.suggest_tags(content, max_suggestions)
            return {"success": True, "suggestions": suggestions}
        except Exception as e:
            return {"error": str(e)}

    def get_tag_stats(self) -> Dict[str, Any]:
        """Get statistics about tag usage in the vault."""
        try:
            stats = self.tag_manager.get_tag_stats()
            return {"success": True, "stats": stats}
        except Exception as e:
            return {"error": str(e)} 