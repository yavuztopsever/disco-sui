from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import shutil
import os

class CreateFolderTool(BaseTool):
    name = "create_folder"
    description = "Create a new folder in the vault"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to create the folder at, relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, path: str) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            folder_path = self._get_full_path(path)

            # Create the folder
            self._ensure_path_exists(folder_path)

            return {
                "success": True,
                "message": f"Folder '{path}' created successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create folder: {str(e)}",
                "error": str(e)
            }

class DeleteFolderTool(BaseTool):
    name = "delete_folder"
    description = "Delete a folder from the vault"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the folder to delete, relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, path: str) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            folder_path = self._get_full_path(path)

            # Check if folder exists
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"Folder not found: {path}")

            # Delete the folder and its contents
            shutil.rmtree(folder_path)

            return {
                "success": True,
                "message": f"Folder '{path}' deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete folder: {str(e)}",
                "error": str(e)
            }

class MoveFolderTool(BaseTool):
    name = "move_folder"
    description = "Move a folder to a new location in the vault"
    inputs = {
        "source": {
            "type": "string",
            "description": "The path to the folder to move, relative to the vault root"
        },
        "destination": {
            "type": "string",
            "description": "The new path for the folder, relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, source: str, destination: str) -> Dict[str, Any]:
        try:
            # Validate paths
            if not self._validate_path(source) or not self._validate_path(destination):
                raise ValueError("Invalid source or destination path")

            # Get full paths
            source_path = self._get_full_path(source)
            dest_path = self._get_full_path(destination)

            # Check if source exists
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Source folder not found: {source}")

            # Move the folder
            shutil.move(source_path, dest_path)

            return {
                "success": True,
                "message": f"Folder moved from '{source}' to '{destination}' successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to move folder: {str(e)}",
                "error": str(e)
            }

class ListFoldersTool(BaseTool):
    name = "list_folders"
    description = "List all folders in the vault"
    inputs = {
        "path": {
            "type": "string",
            "description": "Optional path to list folders from, relative to the vault root",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, path: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get the target directory
            target_dir = self._get_full_path(path) if path else self.vault_path

            # Validate path
            if not self._validate_path(target_dir):
                raise ValueError(f"Invalid path: {path}")

            # List all folders
            folders = []
            for root, dirs, _ in os.walk(target_dir):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    rel_path = os.path.relpath(dir_path, self.vault_path)
                    folders.append(rel_path)

            return {
                "success": True,
                "folders": folders
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list folders: {str(e)}",
                "error": str(e)
            }

class GetFolderContentsTool(BaseTool):
    name = "get_folder_contents"
    description = "Get the contents of a folder, including both files and subfolders"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the folder to get contents from, relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, path: str) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid path: {path}")

            # Get full path
            folder_path = self._get_full_path(path)

            # Check if folder exists
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"Folder not found: {path}")

            # Get contents
            contents = {
                "files": [],
                "folders": []
            }

            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                rel_path = os.path.relpath(item_path, self.vault_path)
                
                if os.path.isfile(item_path) and item.endswith('.md'):
                    contents["files"].append(rel_path)
                elif os.path.isdir(item_path):
                    contents["folders"].append(rel_path)

            return {
                "success": True,
                "contents": contents
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get folder contents: {str(e)}",
                "error": str(e)
            } 