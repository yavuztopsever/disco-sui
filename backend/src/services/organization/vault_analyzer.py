"""Vault structure analyzer implementation."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import os
import re

from ...core.exceptions import AnalysisError
from ..base_service import BaseService


class VaultAnalyzer(BaseService):
    """Service for analyzing vault structure."""
    
    def __init__(self):
        """Initialize the vault analyzer."""
        super().__init__()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the vault analyzer."""
        if self._initialized:
            return
        
        self._initialized = True
    
    async def analyze_structure(
        self,
        vault_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze vault structure.
        
        Args:
            vault_path: Path to vault
            include_patterns: Optional patterns to include
            exclude_patterns: Optional patterns to exclude
            
        Returns:
            Dictionary containing vault structure
            
        Raises:
            AnalysisError: If analysis fails
        """
        try:
            structure = {
                "root": str(vault_path),
                "folders": {},
                "files": []
            }
            
            for root, dirs, files in os.walk(vault_path):
                rel_root = Path(root).relative_to(vault_path)
                
                # Filter directories
                if exclude_patterns:
                    dirs[:] = [d for d in dirs if not any(
                        re.match(p, str(rel_root / d)) for p in exclude_patterns
                    )]
                if include_patterns:
                    dirs[:] = [d for d in dirs if any(
                        re.match(p, str(rel_root / d)) for p in include_patterns
                    )]
                
                # Add folders to structure
                current = structure["folders"]
                for part in rel_root.parts:
                    if part not in current:
                        current[part] = {"folders": {}, "files": []}
                    current = current[part]["folders"]
                
                # Add files to current folder
                for file in files:
                    if file.endswith(".md"):
                        file_path = rel_root / file
                        if (not exclude_patterns or not any(
                            re.match(p, str(file_path)) for p in exclude_patterns
                        )) and (not include_patterns or any(
                            re.match(p, str(file_path)) for p in include_patterns
                        )):
                            if str(rel_root) == ".":
                                structure["files"].append(file)
                            else:
                                current = structure["folders"]
                                for part in rel_root.parts:
                                    current = current[part]["folders"]
                                current[rel_root.parts[-1]]["files"].append(file)
            
            return structure
        except Exception as e:
            raise AnalysisError(f"Failed to analyze vault structure: {str(e)}")
    
    async def compute_stats(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Compute statistics from vault structure.
        
        Args:
            structure: Vault structure
            
        Returns:
            Dictionary containing statistics
            
        Raises:
            AnalysisError: If computation fails
        """
        try:
            stats = {
                "total_files": 0,
                "total_folders": 0,
                "max_depth": 0,
                "avg_files_per_folder": 0
            }
            
            def process_folder(folder: Dict[str, Any], depth: int = 0) -> None:
                stats["total_files"] += len(folder.get("files", []))
                subfolder_count = len(folder.get("folders", {}))
                stats["total_folders"] += subfolder_count
                stats["max_depth"] = max(stats["max_depth"], depth)
                
                for subfolder in folder.get("folders", {}).values():
                    process_folder(subfolder, depth + 1)
            
            process_folder(structure)
            
            if stats["total_folders"] > 0:
                stats["avg_files_per_folder"] = stats["total_files"] / stats["total_folders"]
            
            return stats
        except Exception as e:
            raise AnalysisError(f"Failed to compute vault statistics: {str(e)}")
    
    async def generate_recommendations(
        self,
        structure: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for vault structure.
        
        Args:
            structure: Vault structure
            stats: Vault statistics
            
        Returns:
            List of recommendations
            
        Raises:
            AnalysisError: If recommendation generation fails
        """
        try:
            recommendations = []
            
            # Check folder depth
            if stats["max_depth"] > 5:
                recommendations.append(
                    "Consider reducing folder depth to improve navigation"
                )
            
            # Check files per folder
            if stats["avg_files_per_folder"] > 20:
                recommendations.append(
                    "Consider splitting large folders into smaller, focused categories"
                )
            
            # Check root files
            if len(structure["files"]) > 10:
                recommendations.append(
                    "Consider organizing root-level files into appropriate folders"
                )
            
            return recommendations
        except Exception as e:
            raise AnalysisError(f"Failed to generate recommendations: {str(e)}")
    
    async def plan_reorganization(
        self,
        vault_path: Path,
        target_structure: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Plan vault reorganization.
        
        Args:
            vault_path: Path to vault
            target_structure: Target structure
            
        Returns:
            List of planned changes
            
        Raises:
            AnalysisError: If planning fails
        """
        try:
            current_structure = await self.analyze_structure(vault_path)
            changes = []
            
            def plan_moves(
                current: Dict[str, Any],
                target: Dict[str, Any],
                current_path: Path,
                target_path: Path
            ) -> None:
                # Plan file moves
                for file in current.get("files", []):
                    source = current_path / file
                    if file not in target.get("files", []):
                        # Find best target folder based on content analysis
                        # This is a placeholder - actual implementation would use
                        # content analysis to determine the best target folder
                        dest = target_path / file
                        changes.append({
                            "source": str(source),
                            "destination": str(dest)
                        })
                
                # Recursively plan subfolder moves
                for folder, content in current.get("folders", {}).items():
                    if folder not in target.get("folders", {}):
                        # Find best target folder based on content analysis
                        # This is a placeholder - actual implementation would use
                        # content analysis to determine the best target folder
                        new_target = target_path
                    else:
                        new_target = target_path / folder
                    
                    plan_moves(
                        content,
                        target.get("folders", {}).get(folder, {}),
                        current_path / folder,
                        new_target
                    )
            
            plan_moves(
                current_structure,
                target_structure,
                vault_path,
                vault_path
            )
            
            return changes
        except Exception as e:
            raise AnalysisError(f"Failed to plan reorganization: {str(e)}")
    
    async def apply_reorganization(self, changes: List[Dict[str, str]]) -> None:
        """Apply planned reorganization changes.
        
        Args:
            changes: List of changes to apply
            
        Raises:
            AnalysisError: If applying changes fails
        """
        try:
            for change in changes:
                source = Path(change["source"])
                dest = Path(change["destination"])
                
                # Create parent directories if they don't exist
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                source.rename(dest)
        except Exception as e:
            raise AnalysisError(f"Failed to apply reorganization: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False 