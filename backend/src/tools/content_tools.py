from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import re

class ReplaceContentTool(BaseTool):
    name = "replace_content"
    description = "Replace content in a note"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note, relative to the vault root"
        },
        "search": {
            "type": "string",
            "description": "The text to search for"
        },
        "replace": {
            "type": "string",
            "description": "The text to replace with"
        },
        "regex": {
            "type": "boolean",
            "description": "Whether to use regex for search",
            "default": False
        }
    }
    output_type = "object"

    def forward(self, path: str, search: str, replace: str, regex: bool = False) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            file_path = self._get_full_path(path)

            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Note not found: {path}")

            # Read content
            content = self._read_file(file_path)

            # Perform replacement
            if regex:
                try:
                    pattern = re.compile(search)
                    new_content = pattern.sub(replace, content)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern: {str(e)}")
            else:
                new_content = content.replace(search, replace)

            # Write updated content
            self._write_file(file_path, new_content)

            # Count replacements
            if regex:
                count = len(re.findall(search, content))
            else:
                count = content.count(search)

            return {
                "success": True,
                "message": f"Replaced {count} occurrences in note '{path}' successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to replace content: {str(e)}",
                "error": str(e)
            }

class AppendContentTool(BaseTool):
    name = "append_content"
    description = "Append content to a note"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note, relative to the vault root"
        },
        "content": {
            "type": "string",
            "description": "The content to append"
        },
        "separator": {
            "type": "string",
            "description": "Optional separator to add before the new content",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, path: str, content: str, separator: Optional[str] = None) -> Dict[str, Any]:
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

            # Prepare new content
            new_content = existing_content
            if not new_content.endswith('\n'):
                new_content += '\n'
            if separator:
                new_content += separator + '\n'
            new_content += content

            # Write updated content
            self._write_file(file_path, new_content)

            return {
                "success": True,
                "message": f"Content appended to note '{path}' successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to append content: {str(e)}",
                "error": str(e)
            }

class PrependContentTool(BaseTool):
    name = "prepend_content"
    description = "Prepend content to a note"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note, relative to the vault root"
        },
        "content": {
            "type": "string",
            "description": "The content to prepend"
        },
        "separator": {
            "type": "string",
            "description": "Optional separator to add after the new content",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, path: str, content: str, separator: Optional[str] = None) -> Dict[str, Any]:
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

            # Prepare new content
            new_content = content
            if separator:
                new_content += separator + '\n'
            if existing_content and not existing_content.startswith('\n'):
                new_content += '\n'
            new_content += existing_content

            # Write updated content
            self._write_file(file_path, new_content)

            return {
                "success": True,
                "message": f"Content prepended to note '{path}' successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to prepend content: {str(e)}",
                "error": str(e)
            }

class InsertContentTool(BaseTool):
    name = "insert_content"
    description = "Insert content at a specific position in a note"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note, relative to the vault root"
        },
        "content": {
            "type": "string",
            "description": "The content to insert"
        },
        "position": {
            "type": "integer",
            "description": "The position to insert at (0-based)"
        }
    }
    output_type = "object"

    def forward(self, path: str, content: str, position: int) -> Dict[str, Any]:
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

            # Split content into lines
            lines = existing_content.split('\n')

            # Validate position
            if position < 0 or position > len(lines):
                raise ValueError(f"Invalid position: {position}")

            # Insert content
            lines.insert(position, content)

            # Join lines back together
            new_content = '\n'.join(lines)

            # Write updated content
            self._write_file(file_path, new_content)

            return {
                "success": True,
                "message": f"Content inserted at position {position} in note '{path}' successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to insert content: {str(e)}",
                "error": str(e)
            }

class ExtractContentTool(BaseTool):
    name = "extract_content"
    description = "Extract content from a note using regex pattern"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note, relative to the vault root"
        },
        "pattern": {
            "type": "string",
            "description": "The regex pattern to match"
        },
        "group": {
            "type": "integer",
            "description": "The capture group to extract (0 for full match)",
            "default": 0
        }
    }
    output_type = "object"

    def forward(self, path: str, pattern: str, group: int = 0) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            file_path = self._get_full_path(path)

            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Note not found: {path}")

            # Read content
            content = self._read_file(file_path)

            # Compile pattern
            try:
                regex = re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {str(e)}")

            # Find matches
            matches = regex.finditer(content)
            extracted = [match.group(group) for match in matches]

            return {
                "success": True,
                "matches": extracted
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to extract content: {str(e)}",
                "error": str(e)
            } 