from typing import Dict, Any, Optional, List
from .base_tools import BaseTool, FrontmatterManagerTool
import os
import json
from datetime import datetime
import re
from smolagents import Tool

class HierarchyManagerTool(BaseTool):
    name = "hierarchy_manager"
    description = "Comprehensive hierarchy management for Obsidian notes"
    inputs = {
        "action": {
            "type": "string",
            "description": "The action to perform",
            "enum": ["create", "update", "get_path", "list_children", "maintain", "visualize"]
        },
        "title": {
            "type": "string",
            "description": "The title of the node (required for create)",
            "nullable": True
        },
        "node_type": {
            "type": "string",
            "description": "The type of node (required for create)",
            "enum": ["Category", "Document", "Note", "Code", "Log", "Main", "Person"],
            "nullable": True
        },
        "path": {
            "type": "string",
            "description": "The path to the note (required for update, get_path, list_children)",
            "nullable": True
        },
        "parent": {
            "type": "string",
            "description": "The parent node (using Obsidian link format [[parent]])",
            "nullable": True
        },
        "tags": {
            "type": "array",
            "description": "List of tags for the node",
            "items": {
                "type": "string"
            },
            "nullable": True
        },
        "related_links": {
            "type": "array",
            "description": "List of related nodes (using Obsidian link format [[node]])",
            "items": {
                "type": "string"
            },
            "nullable": True
        },
        "content": {
            "type": "string",
            "description": "Additional content for the node",
            "nullable": True
        },
        "max_items": {
            "type": "integer",
            "description": "Maximum items per node for maintenance",
            "nullable": True
        }
    }
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path
        self.frontmatter_manager = FrontmatterManagerTool()

    def forward(self, action: str, **kwargs) -> Dict[str, Any]:
        try:
            if action == "create":
                if not kwargs.get("title") or not kwargs.get("node_type"):
                    raise ValueError("Title and node_type are required for create action")
                return self.create_node(**kwargs)
            elif action == "update":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for update action")
                return self.update_node(**kwargs)
            elif action == "get_path":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for get_path action")
                return self.get_hierarchy_path(kwargs["path"])
            elif action == "list_children":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for list_children action")
                return self.list_children(kwargs["path"])
            elif action == "maintain":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for maintain action")
                return self.maintain_hierarchy(kwargs["path"], kwargs.get("max_items", 7))
            elif action == "visualize":
                if not kwargs.get("path"):
                    raise ValueError("Path is required for visualize action")
                return self.visualize_hierarchy(kwargs["path"])
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            return {"error": str(e)}

    def create_node(self, title: str, node_type: str, parent: Optional[str] = None,
                   tags: Optional[List[str]] = None, related_links: Optional[List[str]] = None,
                   content: Optional[str] = None) -> Dict[str, Any]:
        """Create a new node in the hierarchy."""
        try:
            # Validate and sanitize the title
            title = title.strip()
            if not title:
                raise ValueError("Title cannot be empty")

            # Create the note file path
            file_path = os.path.join(self.vault_path, f"{title}.md")

            # Prepare frontmatter
            frontmatter = {
                "type": f"#{node_type}",
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "modified_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if parent:
                frontmatter["parent"] = parent
            if tags:
                frontmatter["tags"] = tags
            if related_links:
                frontmatter["related_links"] = related_links

            # Create note content
            note_content = f"---\n{json.dumps(frontmatter, indent=2)}\n---\n\n{content or ''}"
            
            # Write note
            self._write_file(file_path, note_content)
            return {"success": True, "message": f"Created {node_type} node '{title}' successfully"}
        except Exception as e:
            return {"error": str(e)}

    def update_node(self, path: str, parent: Optional[str] = None,
                   related_links: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update a node in the hierarchy."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.frontmatter_manager.get_frontmatter(content)

            # Update frontmatter
            if parent is not None:
                frontmatter["parent"] = parent
            if related_links is not None:
                frontmatter["related_links"] = related_links
            frontmatter["modified_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update content
            updated_content = self.frontmatter_manager.update_frontmatter(content, frontmatter)
            self._write_file(file_path, updated_content)

            return {
                "success": True,
                "message": f"Hierarchy relations updated for note '{path}'"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to update hierarchy relations: {str(e)}",
                "error": str(e)
            }

    def get_hierarchy_path(self, path: str) -> Dict[str, Any]:
        """Get the full path of a node in the hierarchy."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.frontmatter_manager.get_frontmatter(content)
            
            path_list = [path]
            current = frontmatter.get("parent")
            
            while current:
                path_list.insert(0, current)
                parent_path = self._get_full_path(current)
                parent_content = self._read_file(parent_path)
                parent_frontmatter = self.frontmatter_manager.get_frontmatter(parent_content)
                current = parent_frontmatter.get("parent")
            
            return {"success": True, "path": path_list}
        except Exception as e:
            return {"error": str(e)}

    def list_children(self, path: str) -> Dict[str, Any]:
        """List all child nodes of a note."""
        try:
            children = []
            for file_path in self._list_files(self.vault_path):
                content = self._read_file(file_path)
                frontmatter = self.frontmatter_manager.get_frontmatter(content)
                if frontmatter.get("parent") == f"[[{path}]]":
                    children.append(file_path)
            return {"success": True, "children": children}
        except Exception as e:
            return {"error": str(e)}

    def maintain_hierarchy(self, root_path: str, max_items: int = 7) -> Dict[str, Any]:
        """Maintain and optimize the hierarchy structure."""
        try:
            def count_items(path: str) -> int:
                count = 0
                for file_path in self._list_files(os.path.dirname(path)):
                    child_content = self._read_file(file_path)
                    child_frontmatter = self.frontmatter_manager.get_frontmatter(child_content)
                    if child_frontmatter.get("parent") == f"[[{os.path.basename(path)}]]":
                        count += 1
                return count
            
            def split_node(path: str):
                content = self._read_file(path)
                frontmatter = self.frontmatter_manager.get_frontmatter(content)
                title = frontmatter.get("title", os.path.basename(path))
                
                # Create subcategories
                items = []
                for file_path in self._list_files(os.path.dirname(path)):
                    child_content = self._read_file(file_path)
                    child_frontmatter = self.frontmatter_manager.get_frontmatter(child_content)
                    if child_frontmatter.get("parent") == f"[[{title}]]":
                        items.append((file_path, child_content, child_frontmatter))
                
                # Group items into subcategories
                subcategories = {}
                for item_path, item_content, item_frontmatter in items:
                    # TODO: Implement intelligent grouping based on content
                    subcategory = "General"
                    if subcategory not in subcategories:
                        subcategories[subcategory] = []
                    subcategories[subcategory].append((item_path, item_content, item_frontmatter))
                
                # Create subcategory nodes
                for subcategory, subcategory_items in subcategories.items():
                    subcategory_path = self._get_full_path(f"{os.path.dirname(path)}/{subcategory}.md")
                    subcategory_frontmatter = {
                        "type": "Subcategory",
                        "title": subcategory,
                        "parent": f"[[{title}]]",
                        "tags": frontmatter.get("tags", []) + [subcategory.lower().replace(" ", "_")]
                    }
                    subcategory_content = f"---\n{json.dumps(subcategory_frontmatter, indent=2)}\n---\n\n# {subcategory}\n\n## Items\n"
                    
                    # Move items to subcategory
                    for item_path, item_content, item_frontmatter in subcategory_items:
                        new_item_path = os.path.join(os.path.dirname(subcategory_path), os.path.basename(item_path))
                        item_frontmatter["parent"] = f"[[{subcategory}]]"
                        updated_item_content = self.frontmatter_manager.update_frontmatter(item_content, item_frontmatter)
                        self._write_file(new_item_path, updated_item_content)
                    
                    self._write_file(subcategory_path, subcategory_content)
            
            # Check and split nodes with too many items
            for file_path in self._list_files(os.path.dirname(root_path)):
                if count_items(file_path) > max_items:
                    split_node(file_path)
            
            return {"success": True, "message": "Hierarchy maintenance completed successfully"}
        except Exception as e:
            return {"error": str(e)}

    def visualize_hierarchy(self, path: str) -> Dict[str, Any]:
        """Generate a visual representation of the hierarchy."""
        try:
            def build_tree(current_path: str, depth: int = 0) -> Dict[str, Any]:
                content = self._read_file(current_path)
                frontmatter = self.frontmatter_manager.get_frontmatter(content)
                
                node = {
                    "name": os.path.basename(current_path),
                    "type": frontmatter.get("type", "Unknown"),
                    "children": []
                }
                
                # Get children
                for file_path in self._list_files(os.path.dirname(current_path)):
                    child_content = self._read_file(file_path)
                    child_frontmatter = self.frontmatter_manager.get_frontmatter(child_content)
                    if child_frontmatter.get("parent") == f"[[{os.path.basename(current_path)}]]":
                        node["children"].append(build_tree(file_path, depth + 1))
                
                return node
            
            tree = build_tree(path)
            return {"success": True, "tree": tree}
        except Exception as e:
            return {"error": str(e)} 