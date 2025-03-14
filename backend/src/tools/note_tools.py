from typing import Dict, Any, Optional, List
from .base_tools import BaseTool

class CreateNoteTool(BaseTool):
    name = "create_note"
    description = "Create a new note in the vault"
    inputs = {
        "title": {
            "type": "string",
            "description": "The title of the note"
        },
        "content": {
            "type": "string",
            "description": "The content of the note"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where to create the note",
            "nullable": True
        },
        "frontmatter": {
            "type": "object",
            "description": "Optional frontmatter data for the note",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, title: str, content: str, folder: Optional[str] = None, frontmatter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Validate and sanitize the title
            title = title.strip()
            if not title:
                raise ValueError("Title cannot be empty")

            # Create folder path if specified
            folder_path = self._get_full_path(folder) if folder else self.vault_path
            self._ensure_path_exists(folder_path)

            # Create the note file path
            file_path = os.path.join(folder_path, f"{title}.md")

            # Prepare content with frontmatter if provided
            if frontmatter:
                content = self._update_frontmatter(content, frontmatter)

            # Write the note
            self._write_file(file_path, content)

            return {
                "success": True,
                "message": f"Note '{title}' created successfully",
                "path": os.path.relpath(file_path, self.vault_path)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create note: {str(e)}",
                "error": str(e)
            }

class UpdateNoteTool(BaseTool):
    name = "update_note"
    description = "Update an existing note in the vault"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note relative to the vault root"
        },
        "content": {
            "type": "string",
            "description": "The new content for the note"
        },
        "frontmatter": {
            "type": "object",
            "description": "Optional frontmatter data to update",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, path: str, content: str, frontmatter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            file_path = self._get_full_path(path)

            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Note not found: {path}")

            # Read existing content
            existing_content = self._read_file(file_path)
            existing_frontmatter = self._get_frontmatter(existing_content)

            # Update frontmatter if provided
            if frontmatter:
                existing_frontmatter.update(frontmatter)
                content = self._update_frontmatter(content, existing_frontmatter)

            # Write updated content
            self._write_file(file_path, content)

            return {
                "success": True,
                "message": f"Note '{path}' updated successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to update note: {str(e)}",
                "error": str(e)
            }

class DeleteNoteTool(BaseTool):
    name = "delete_note"
    description = "Delete a note from the vault"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, path: str) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            file_path = self._get_full_path(path)

            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Note not found: {path}")

            # Delete the file
            os.remove(file_path)

            return {
                "success": True,
                "message": f"Note '{path}' deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete note: {str(e)}",
                "error": str(e)
            }

class ListNotesTool(BaseTool):
    name = "list_notes"
    description = "List all notes in the vault"
    inputs = {
        "folder": {
            "type": "string",
            "description": "Optional folder path to list notes from",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get the target directory
            target_dir = self._get_full_path(folder) if folder else self.vault_path

            # Validate path
            if not self._validate_path(target_dir):
                raise ValueError(f"Invalid folder path: {folder}")

            # List all markdown files
            notes = self._list_files(target_dir)

            return {
                "success": True,
                "notes": notes
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list notes: {str(e)}",
                "error": str(e)
            }

class SearchNotesTool(BaseTool):
    name = "search_notes"
    description = "Search for notes containing specific text"
    inputs = {
        "query": {
            "type": "string",
            "description": "The text to search for in notes"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path to search in",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, query: str, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get the target directory
            target_dir = self._get_full_path(folder) if folder else self.vault_path

            # Validate path
            if not self._validate_path(target_dir):
                raise ValueError(f"Invalid folder path: {folder}")

            # Search for notes
            results = []
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        content = self._read_file(file_path)
                        if query.lower() in content.lower():
                            rel_path = os.path.relpath(file_path, self.vault_path)
                            results.append({
                                "path": rel_path,
                                "matches": content.lower().count(query.lower())
                            })

            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to search notes: {str(e)}",
                "error": str(e)
            } 