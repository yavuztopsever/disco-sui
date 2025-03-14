from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import os
import json
from datetime import datetime
import shutil
from collections import defaultdict

class AnalyzeVaultStructureTool(BaseTool):
    name = "analyze_vault_structure"
    description = "Analyze the current vault structure and provide insights"
    inputs = {
        "include_hidden": {
            "type": "boolean",
            "description": "Whether to include hidden files and folders",
            "default": False
        }
    }
    output_type = "object"

    def forward(self, include_hidden: bool = False) -> Dict[str, Any]:
        try:
            # Initialize statistics
            stats = {
                "total_files": 0,
                "total_folders": 0,
                "file_types": defaultdict(int),
                "folder_sizes": defaultdict(int),
                "folder_depths": defaultdict(int),
                "orphaned_files": [],
                "empty_folders": [],
                "large_files": [],
                "recent_files": []
            }

            # Walk through vault
            for root, dirs, files in os.walk(self.vault_path):
                # Skip hidden files/folders if not included
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]

                # Get relative path
                rel_path = os.path.relpath(root, self.vault_path)
                if rel_path == '.':
                    rel_path = ''

                # Count folders
                stats["total_folders"] += 1
                stats["folder_depths"][rel_path] = rel_path.count(os.sep)

                # Process files
                folder_size = 0
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.join(rel_path, file)
                    
                    # Skip if not in vault
                    if not self._validate_path(rel_file_path):
                        continue

                    stats["total_files"] += 1
                    
                    # Get file type
                    ext = os.path.splitext(file)[1].lower()
                    stats["file_types"][ext] += 1

                    # Get file size
                    size = os.path.getsize(file_path)
                    folder_size += size

                    # Track large files (>10MB)
                    if size > 10 * 1024 * 1024:
                        stats["large_files"].append({
                            "path": rel_file_path,
                            "size": size
                        })

                    # Track recent files (modified in last 7 days)
                    mtime = os.path.getmtime(file_path)
                    if datetime.fromtimestamp(mtime) > datetime.now().replace(day=datetime.now().day - 7):
                        stats["recent_files"].append({
                            "path": rel_file_path,
                            "modified": datetime.fromtimestamp(mtime).isoformat()
                        })

                # Store folder size
                stats["folder_sizes"][rel_path] = folder_size

                # Check for empty folders
                if not files and not dirs:
                    stats["empty_folders"].append(rel_path)

            # Sort lists
            stats["large_files"].sort(key=lambda x: x["size"], reverse=True)
            stats["recent_files"].sort(key=lambda x: x["modified"], reverse=True)

            # Save analysis
            analysis_path = os.path.join(self.vault_path, ".obsidian", "vault_analysis.json")
            with open(analysis_path, "w") as f:
                json.dump(stats, f, indent=2)

            return {
                "success": True,
                "message": "Vault structure analysis completed",
                "stats": stats
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to analyze vault structure: {str(e)}",
                "error": str(e)
            }

class ReorganizeVaultTool(BaseTool):
    name = "reorganize_vault"
    description = "Reorganize the vault based on analysis and rules"
    inputs = {
        "rules": {
            "type": "object",
            "description": "Rules for reorganization",
            "properties": {
                "file_types": {
                    "type": "object",
                    "description": "Mapping of file extensions to target folders"
                },
                "max_folder_depth": {
                    "type": "integer",
                    "description": "Maximum allowed folder depth",
                    "default": 5
                },
                "max_file_size": {
                    "type": "integer",
                    "description": "Maximum allowed file size in bytes",
                    "default": 100 * 1024 * 1024  # 100MB
                },
                "consolidate_empty": {
                    "type": "boolean",
                    "description": "Whether to consolidate empty folders",
                    "default": True
                }
            }
        }
    }
    output_type = "object"

    def forward(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Load current analysis
            analysis_path = os.path.join(self.vault_path, ".obsidian", "vault_analysis.json")
            if not os.path.exists(analysis_path):
                return {
                    "success": False,
                    "message": "No vault analysis found. Run analyze_vault_structure first."
                }

            with open(analysis_path, "r") as f:
                analysis = json.load(f)

            # Track changes
            changes = {
                "moved_files": [],
                "deleted_folders": [],
                "created_folders": [],
                "errors": []
            }

            # Process files based on type rules
            if "file_types" in rules:
                for root, _, files in os.walk(self.vault_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.vault_path)
                        
                        # Skip if not in vault
                        if not self._validate_path(rel_path):
                            continue

                        # Get file extension
                        ext = os.path.splitext(file)[1].lower()
                        if ext in rules["file_types"]:
                            target_folder = rules["file_types"][ext]
                            target_path = os.path.join(self.vault_path, target_folder)
                            
                            # Create target folder if needed
                            if not os.path.exists(target_path):
                                os.makedirs(target_path)
                                changes["created_folders"].append(target_folder)

                            # Move file
                            new_path = os.path.join(target_path, file)
                            if file_path != new_path:
                                try:
                                    shutil.move(file_path, new_path)
                                    changes["moved_files"].append({
                                        "from": rel_path,
                                        "to": os.path.relpath(new_path, self.vault_path)
                                    })
                                except Exception as e:
                                    changes["errors"].append(f"Failed to move {rel_path}: {str(e)}")

            # Check folder depths
            if "max_folder_depth" in rules:
                for folder, depth in analysis["folder_depths"].items():
                    if depth > rules["max_folder_depth"]:
                        changes["errors"].append(
                            f"Folder '{folder}' exceeds maximum depth of {rules['max_folder_depth']}"
                        )

            # Check file sizes
            if "max_file_size" in rules:
                for file_info in analysis["large_files"]:
                    if file_info["size"] > rules["max_file_size"]:
                        changes["errors"].append(
                            f"File '{file_info['path']}' exceeds maximum size of {rules['max_file_size']} bytes"
                        )

            # Consolidate empty folders
            if rules.get("consolidate_empty", True):
                for folder in analysis["empty_folders"]:
                    try:
                        os.rmdir(os.path.join(self.vault_path, folder))
                        changes["deleted_folders"].append(folder)
                    except Exception as e:
                        changes["errors"].append(f"Failed to delete empty folder '{folder}': {str(e)}")

            # Save changes
            changes_path = os.path.join(self.vault_path, ".obsidian", "reorganization_changes.json")
            with open(changes_path, "w") as f:
                json.dump(changes, f, indent=2)

            return {
                "success": True,
                "message": "Vault reorganization completed",
                "changes": changes
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to reorganize vault: {str(e)}",
                "error": str(e)
            }

class SuggestOrganizationTool(BaseTool):
    name = "suggest_organization"
    description = "Suggest organization rules based on vault analysis"
    inputs = {
        "min_file_count": {
            "type": "integer",
            "description": "Minimum number of files to suggest a folder",
            "default": 5
        }
    }
    output_type = "object"

    def forward(self, min_file_count: int = 5) -> Dict[str, Any]:
        try:
            # Load current analysis
            analysis_path = os.path.join(self.vault_path, ".obsidian", "vault_analysis.json")
            if not os.path.exists(analysis_path):
                return {
                    "success": False,
                    "message": "No vault analysis found. Run analyze_vault_structure first."
                }

            with open(analysis_path, "r") as f:
                analysis = json.load(f)

            # Analyze file types
            file_type_suggestions = {}
            for ext, count in analysis["file_types"].items():
                if count >= min_file_count:
                    # Suggest folder based on file type
                    folder_name = ext[1:].upper() + "_files" if ext else "other_files"
                    file_type_suggestions[ext] = folder_name

            # Analyze folder sizes
            large_folders = []
            for folder, size in analysis["folder_sizes"].items():
                if size > 100 * 1024 * 1024:  # 100MB
                    large_folders.append({
                        "folder": folder,
                        "size": size
                    })

            # Analyze folder depths
            deep_folders = []
            for folder, depth in analysis["folder_depths"].items():
                if depth > 5:
                    deep_folders.append({
                        "folder": folder,
                        "depth": depth
                    })

            # Generate suggestions
            suggestions = {
                "file_type_rules": file_type_suggestions,
                "max_folder_depth": 5,
                "max_file_size": 100 * 1024 * 1024,  # 100MB
                "consolidate_empty": True,
                "warnings": {
                    "large_folders": large_folders,
                    "deep_folders": deep_folders,
                    "orphaned_files": analysis["orphaned_files"],
                    "empty_folders": analysis["empty_folders"]
                }
            }

            # Save suggestions
            suggestions_path = os.path.join(self.vault_path, ".obsidian", "organization_suggestions.json")
            with open(suggestions_path, "w") as f:
                json.dump(suggestions, f, indent=2)

            return {
                "success": True,
                "message": "Organization suggestions generated",
                "suggestions": suggestions
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to generate organization suggestions: {str(e)}",
                "error": str(e)
            } 