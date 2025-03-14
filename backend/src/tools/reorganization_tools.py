from typing import Dict, Any, Optional, List
from pathlib import Path
from ..core.tool_interfaces import OrganizationTool
import os
import json
from datetime import datetime
import shutil
from collections import defaultdict

class AnalyzeVaultTool(OrganizationTool):
    """Tool for analyzing vault structure."""
    name = "analyze_vault"
    description = "Analyze the current vault structure"
    
    async def forward(
        self,
        directory: Optional[str] = None,
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """Analyze vault structure.
        
        Args:
            directory: Optional directory to analyze
            pattern: File pattern to match
            
        Returns:
            Dictionary containing analysis results
        """
        return await self.analyze_structure(
            Path(directory) if directory else None,
            pattern
        )

class ReorganizeVaultTool(OrganizationTool):
    """Tool for reorganizing vault content."""
    name = "reorganize_vault"
    description = "Reorganize vault content based on rules"
    
    async def forward(
        self,
        rules: Dict[str, Any],
        directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reorganize vault content.
        
        Args:
            rules: Reorganization rules
            directory: Optional directory to reorganize
            
        Returns:
            Dictionary containing reorganization results
        """
        return await self.reorganize(
            rules,
            Path(directory) if directory else None
        )

class VaultOrganizationTool(OrganizationTool):
    """Tool for analyzing and organizing vault structure."""
    name = "vault_organization"
    description = "Analyze and organize vault structure"
    
    async def forward(
        self,
        action: str = "analyze",
        rules: Optional[Dict[str, Any]] = None,
        min_file_count: int = 5,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """Analyze or reorganize vault structure.
        
        Args:
            action: Action to perform ("analyze", "suggest", "reorganize")
            rules: Rules for reorganization
            min_file_count: Minimum file count for suggestions
            include_hidden: Whether to include hidden files
            
        Returns:
            Dictionary containing analysis or reorganization results
        """
        try:
            # Analyze vault structure
            analysis = await self._analyze_structure(include_hidden)
            
            if action == "analyze":
                return {
                    "success": True,
                    "analysis": analysis
                }
            
            elif action == "suggest":
                suggestions = await self._generate_suggestions(analysis, min_file_count)
                return {
                    "success": True,
                    "suggestions": suggestions
                }
            
            elif action == "reorganize":
                if not rules:
                    raise ValueError("Rules must be provided for reorganization")
                result = await self._reorganize_vault(analysis, rules)
                return {
                    "success": True,
                    "reorganization": result
                }
            
            else:
                raise ValueError(f"Invalid action: {action}")
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_structure(self, include_hidden: bool = False) -> Dict[str, Any]:
        """Analyze vault structure.
        
        Args:
            include_hidden: Whether to include hidden files
            
        Returns:
            Dictionary containing analysis results
        """
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
                if (datetime.now().timestamp() - mtime) < 7 * 24 * 60 * 60:
                    stats["recent_files"].append({
                        "path": rel_file_path,
                        "modified": datetime.fromtimestamp(mtime).isoformat()
                    })
            
            # Update folder size
            stats["folder_sizes"][rel_path] = folder_size
            
            # Track empty folders
            if not files and not dirs:
                stats["empty_folders"].append(rel_path)
        
        return stats
    
    async def _generate_suggestions(
        self,
        analysis: Dict[str, Any],
        min_file_count: int = 5
    ) -> Dict[str, Any]:
        """Generate organization suggestions.
        
        Args:
            analysis: Analysis results
            min_file_count: Minimum file count for suggestions
            
        Returns:
            Dictionary containing suggestions
        """
        # Generate file type rules
        file_type_suggestions = {}
        for ext, count in analysis["file_types"].items():
            if count >= min_file_count:
                suggested_folder = ext.strip('.').upper() + "_Files"
                file_type_suggestions[ext] = suggested_folder
        
        # Identify large folders
        large_folders = []
        for folder, size in analysis["folder_sizes"].items():
            if size > 100 * 1024 * 1024:  # 100MB
                large_folders.append({
                    "path": folder,
                    "size": size
                })
        
        # Identify deep folders
        deep_folders = []
        for folder, depth in analysis["folder_depths"].items():
            if depth > 5:
                deep_folders.append({
                    "path": folder,
                    "depth": depth
                })
        
        return {
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
    
    async def _reorganize_vault(
        self,
        analysis: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reorganize vault based on rules.
        
        Args:
            analysis: Analysis results
            rules: Reorganization rules
            
        Returns:
            Dictionary containing reorganization results
        """
        changes = {
            "moved_files": [],
            "consolidated_folders": [],
            "errors": []
        }
        
        try:
            # Apply file type rules
            if "file_types" in rules:
                for root, _, files in os.walk(self.vault_path):
                    for file in files:
                        try:
                            ext = os.path.splitext(file)[1].lower()
                            if ext in rules["file_types"]:
                                old_path = os.path.join(root, file)
                                target_folder = os.path.join(
                                    self.vault_path,
                                    rules["file_types"][ext]
                                )
                                os.makedirs(target_folder, exist_ok=True)
                                new_path = os.path.join(target_folder, file)
                                shutil.move(old_path, new_path)
                                changes["moved_files"].append({
                                    "file": file,
                                    "from": os.path.relpath(old_path, self.vault_path),
                                    "to": os.path.relpath(new_path, self.vault_path)
                                })
                        except Exception as e:
                            changes["errors"].append({
                                "file": file,
                                "error": str(e)
                            })
            
            # Consolidate empty folders
            if rules.get("consolidate_empty", True):
                for folder in analysis["empty_folders"]:
                    try:
                        folder_path = os.path.join(self.vault_path, folder)
                        if os.path.exists(folder_path):
                            os.rmdir(folder_path)
                            changes["consolidated_folders"].append(folder)
                    except Exception as e:
                        changes["errors"].append({
                            "folder": folder,
                            "error": str(e)
                        })
            
            return changes
            
        except Exception as e:
            raise ValueError(f"Failed to reorganize vault: {str(e)}")

# Remove old classes
if "AnalyzeVaultStructureTool" in globals():
    del AnalyzeVaultStructureTool
if "ReorganizeVaultTool" in globals():
    del ReorganizeVaultTool
if "SuggestOrganizationTool" in globals():
    del SuggestOrganizationTool 