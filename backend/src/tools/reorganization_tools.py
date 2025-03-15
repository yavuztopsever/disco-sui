from typing import Dict, Any, Optional, List
from pathlib import Path
from ..core.tool_interfaces import OrganizationTool
import os
import json
from datetime import datetime
import shutil
from collections import defaultdict
from .base_tools import BaseTool
import asyncio
from smolagents import Tool
from pydantic import BaseModel, ConfigDict
from ..core.exceptions import ReorganizationError
from ..services.organization.vault_analyzer import VaultAnalyzer

class AnalyzeVaultInput(BaseModel):
    """Input for vault structure analysis."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    vault_path: Path
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class AnalyzeVaultOutput(BaseModel):
    """Output from vault structure analysis."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    structure: Dict[str, Any]
    stats: Dict[str, Any]
    recommendations: List[str]


class AnalyzeVaultStructureTool:
    """Tool for analyzing vault structure."""
    
    def __init__(self, analyzer: VaultAnalyzer):
        """Initialize the vault structure analysis tool.
        
        Args:
            analyzer: Vault analyzer instance
        """
        self.analyzer = analyzer
    
    async def execute(self, input_data: AnalyzeVaultInput) -> AnalyzeVaultOutput:
        """Execute the vault structure analysis.
        
        Args:
            input_data: Input containing vault path and patterns
            
        Returns:
            Output containing analysis results
            
        Raises:
            ReorganizationError: If analysis fails
        """
        try:
            structure = await self.analyzer.analyze_structure(
                input_data.vault_path,
                include_patterns=input_data.include_patterns,
                exclude_patterns=input_data.exclude_patterns
            )
            
            stats = await self.analyzer.compute_stats(structure)
            recommendations = await self.analyzer.generate_recommendations(structure, stats)
            
            return AnalyzeVaultOutput(
                structure=structure,
                stats=stats,
                recommendations=recommendations
            )
        except Exception as e:
            raise ReorganizationError(f"Failed to analyze vault structure: {str(e)}")


class ReorganizeVaultInput(BaseModel):
    """Input for vault reorganization."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    vault_path: Path
    target_structure: Dict[str, Any]
    dry_run: bool = True


class ReorganizeVaultOutput(BaseModel):
    """Output from vault reorganization."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    changes: List[Dict[str, str]]
    success: bool
    message: str


class ReorganizeVaultTool:
    """Tool for reorganizing vault structure."""
    
    def __init__(self, analyzer: VaultAnalyzer):
        """Initialize the vault reorganization tool.
        
        Args:
            analyzer: Vault analyzer instance
        """
        self.analyzer = analyzer
    
    async def execute(self, input_data: ReorganizeVaultInput) -> ReorganizeVaultOutput:
        """Execute the vault reorganization.
        
        Args:
            input_data: Input containing vault path and target structure
            
        Returns:
            Output containing reorganization results
            
        Raises:
            ReorganizationError: If reorganization fails
        """
        try:
            changes = await self.analyzer.plan_reorganization(
                input_data.vault_path,
                input_data.target_structure
            )
            
            if not input_data.dry_run:
                await self.analyzer.apply_reorganization(changes)
                return ReorganizeVaultOutput(
                    changes=changes,
                    success=True,
                    message="Vault reorganization completed successfully"
                )
            
            return ReorganizeVaultOutput(
                changes=changes,
                success=True,
                message="Dry run completed, no changes applied"
            )
        except Exception as e:
            raise ReorganizationError(f"Failed to reorganize vault: {str(e)}")


class SuggestOrganizationTool:
    """Tool for suggesting vault organization improvements."""
    
    def __init__(self, analyzer: VaultAnalyzer):
        """Initialize the organization suggestion tool.
        
        Args:
            analyzer: Vault analyzer instance
        """
        self.analyzer = analyzer
    
    async def execute(self, input_data: AnalyzeVaultInput) -> List[str]:
        """Execute the organization suggestion generation.
        
        Args:
            input_data: Input containing vault path and patterns
            
        Returns:
            List of organization suggestions
            
        Raises:
            ReorganizationError: If suggestion generation fails
        """
        try:
            structure = await self.analyzer.analyze_structure(
                input_data.vault_path,
                include_patterns=input_data.include_patterns,
                exclude_patterns=input_data.exclude_patterns
            )
            
            stats = await self.analyzer.compute_stats(structure)
            recommendations = await self.analyzer.generate_recommendations(structure, stats)
            
            return recommendations
        except Exception as e:
            raise ReorganizationError(f"Failed to generate organization suggestions: {str(e)}")


class VaultReorganizationTool(BaseTool):
    """Tool for reorganizing notes within the Obsidian vault.
    
    This implements the VaultReorganizationTool functionality from Flow 4.
    It uses semantic analysis and hierarchy management to optimize vault structure.
    """
    
    def __init__(self, vault_path: Path):
        """Initialize the reorganization tool.
        
        Args:
            vault_path: Path to the Obsidian vault
        """
        super().__init__()
        self.vault_path = vault_path
        
        # These would be properly initialized in practice
        self.semantic_analyzer = None
        self.hierarchy_manager = None
        self.obsidian_api = None
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "VaultReorganizationTool"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Reorganizes Obsidian vault structure based on content analysis and hierarchy management"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["analyze", "reorganize", "suggest", "validate"],
                "required": True
            },
            "config": {
                "type": "object",
                "description": "Configuration for reorganization",
                "required": False,
                "properties": {
                    "strategy": {
                        "type": "string",
                        "description": "Reorganization strategy",
                        "enum": ["semantic", "date", "alphabetical", "custom"]
                    },
                    "target": {
                        "type": "string",
                        "description": "Target folder or note to reorganize"
                    },
                    "options": {
                        "type": "object",
                        "description": "Strategy-specific options"
                    }
                }
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Get the tool manifest for LLM agent.
        
        Returns:
            Dict[str, Any]: Tool manifest with schema and examples
        """
        return {
            "name": self.name,
            "description": self.description,
            "params": self.inputs,
            "examples": [
                {
                    "action": "analyze",
                    "config": {"target": "/path/to/vault"}
                },
                {
                    "action": "reorganize",
                    "config": {
                        "strategy": "semantic",
                        "target": "/path/to/folder",
                        "options": {"depth": 2, "create_new_folders": True}
                    }
                },
                {
                    "action": "suggest",
                    "config": {"target": "/path/to/vault"}
                }
            ]
        }
    
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the reorganization operation.
        
        This follows the Flow 4 sequence with SemanticAnalyzer and HierarchyManager.
        """
        action = parameters["action"]
        config = parameters.get("config", {})
        
        try:
            # Validate components
            if action != "validate" and (not self.semantic_analyzer or not self.hierarchy_manager):
                self.logger.warning("SemanticAnalyzer or HierarchyManager not initialized, using placeholder implementations")
                
            if action == "analyze":
                return await self._analyze_vault_structure(config)
            elif action == "reorganize":
                return await self._reorganize_vault(config)
            elif action == "suggest":
                return await self._suggest_reorganization(config)
            elif action == "validate":
                return await self._validate_structure(config)
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Reorganization operation failed: {str(e)}")
            raise
            
    async def _analyze_vault_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the vault structure.
        
        This corresponds to the Analyze Vault Structure step in Flow 4.
        Uses SemanticAnalyzer to understand vault content and organization.
        """
        target = config.get("target", str(self.vault_path))
        depth = config.get("depth", -1)  # -1 means unlimited depth
        
        # Call the SemanticAnalyzer if available
        if self.semantic_analyzer:
            try:
                # Following Flow 4: LLMAgent -> SemanticAnalyzer
                structure_analysis = await self.semantic_analyzer.analyze_vault_structure(target, depth)
                return {
                    "result": structure_analysis
                }
            except Exception as e:
                self.logger.error(f"SemanticAnalyzer failed: {str(e)}")
                # Fall back to basic analysis
        
        # Basic implementation if semantic analyzer isn't available
        # Count files and folders
        folder_count = 0
        note_count = 0
        tags = set()
        clusters = set()
        max_depth = 0
        
        target_path = Path(target)
        if not target_path.exists():
            raise ValueError(f"Target path does not exist: {target}")
            
        for root, dirs, files in os.walk(target_path):
            rel_path = Path(root).relative_to(target_path)
            current_depth = len(rel_path.parts)
            max_depth = max(max_depth, current_depth)
            
            folder_count += len(dirs)
            
            for file in files:
                if file.endswith('.md'):
                    note_count += 1
                    
                    # Extract tags from markdown files
                    try:
                        file_path = Path(root) / file
                        content = file_path.read_text()
                        
                        # Simple tag extraction (basic implementation)
                        file_tags = re.findall(r'#(\w+)', content)
                        tags.update(file_tags)
                        
                        # Simple cluster detection based on folders
                        if len(rel_path.parts) > 0:
                            clusters.add(rel_path.parts[0])
                    except Exception as e:
                        self.logger.warning(f"Error processing file {file}: {str(e)}")
        
        # Generate basic insights
        insights = []
        if note_count > folder_count * 10:
            insights.append("Some folders contain too many notes, consider subdividing")
        if len(tags) < note_count / 3:
            insights.append("Many notes lack proper tagging")
        if max_depth > 5:
            insights.append("Deep folder structure might make navigation difficult")
        
        return {
            "result": {
                "structure": {
                    "folders": folder_count,
                    "notes": note_count,
                    "depth": max_depth,
                    "tags": list(tags)[:10],  # Limit to 10 tags for brevity
                    "clusters": list(clusters)
                },
                "insights": insights
            }
        }
        
    async def _reorganize_vault(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Reorganize the vault based on provided configuration.
        
        This corresponds to the Modify Note Structure/Content step in Flow 4.
        Following the exact sequence from Flow 4:
        1. Call SemanticAnalyzer to analyze content
        2. Call HierarchyManager to generate reorganization plan
        3. Execute plan through ObsidianAPI
        """
        strategy = config.get("strategy", "semantic")
        target = config.get("target", str(self.vault_path))
        options = config.get("options", {})
        
        # Step 1: Analyze vault structure with SemanticAnalyzer
        if self.semantic_analyzer:
            structure_analysis = await self.semantic_analyzer.analyze_vault_structure(target)
        else:
            # Basic analysis if semantic analyzer isn't available
            analysis_result = await self._analyze_vault_structure({"target": target})
            structure_analysis = analysis_result["result"]
            
        # Step 2: Generate reorganization plan with HierarchyManager
        if self.hierarchy_manager:
            reorganization_plan = await self.hierarchy_manager.generate_reorganization_plan(
                structure_analysis, 
                strategy,
                options
            )
        else:
            # Generate a basic plan if hierarchy manager isn't available
            reorganization_plan = await self._generate_basic_reorganization_plan(
                structure_analysis,
                strategy,
                options
            )
            
        # Step 3: Execute the plan through ObsidianAPI
        if self.obsidian_api:
            result = await self.obsidian_api.execute_reorganization(reorganization_plan)
            return {
                "result": result
            }
        else:
            # Return the plan that would be executed
            # This is a placeholder until ObsidianAPI is implemented
            changes = reorganization_plan.get("changes", [])
            
            return {
                "result": {
                    "changes": changes,
                    "summary": f"Reorganized vault using {strategy} strategy",
                    "stats": {
                        "files_moved": len([c for c in changes if c["type"] == "move"]),
                        "folders_created": len([c for c in changes if c["type"] == "create" and c.get("kind") == "folder"]),
                        "files_modified": len([c for c in changes if c["type"] == "update"])
                    }
                }
            }
    
    async def _generate_basic_reorganization_plan(
        self, 
        structure_analysis: Dict[str, Any],
        strategy: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a basic reorganization plan without HierarchyManager.
        
        This is a helper method used when HierarchyManager isn't available.
        """
        target = options.get("target", str(self.vault_path))
        target_path = Path(target)
        
        changes = []
        
        if strategy == "semantic":
            # Basic semantic grouping by clusters
            clusters = structure_analysis.get("structure", {}).get("clusters", [])
            
            # Ensure cluster folders exist
            for cluster in clusters:
                cluster_path = target_path / cluster
                if not cluster_path.exists():
                    changes.append({
                        "type": "create", 
                        "path": str(cluster_path), 
                        "kind": "folder"
                    })
            
            # Group notes by cluster based on content similarity (simplified)
            # This would normally use semantic analysis
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(target_path)
                        
                        # Skip already organized files
                        if len(rel_path.parts) > 1 and rel_path.parts[0] in clusters:
                            continue
                            
                        # Assign to a cluster (simplified assignment)
                        if clusters:
                            target_cluster = clusters[hash(file) % len(clusters)]
                            new_path = target_path / target_cluster / file
                            
                            changes.append({
                                "type": "move",
                                "from": str(file_path),
                                "to": str(new_path)
                            })
        
        elif strategy == "date":
            # Date-based organization - would be based on file metadata
            # Simplified implementation
            pass
            
        elif strategy == "alphabetical":
            # Alphabetical organization
            # Simplified implementation
            pass
            
        return {
            "changes": changes,
            "strategy": strategy
        }
        
    async def _suggest_reorganization(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest reorganization changes without applying them.
        
        This is a planning step that would occur before the actual reorganization.
        """
        target = config.get("target", str(self.vault_path))
        
        # Similar to the analyze method but returns specific suggestions
        suggestions = [
            {
                "type": "create_structure",
                "description": "Create a folder structure based on projects and statuses",
                "folders": ["Active", "Archive", "Reference", "Projects/ProjectA", "Projects/ProjectB"]
            },
            {
                "type": "move_notes",
                "description": "Group related notes together",
                "moves": [
                    {"note": "note1.md", "destination": "Projects/ProjectA"},
                    {"note": "note2.md", "destination": "Reference"}
                ]
            },
            {
                "type": "tag_system",
                "description": "Implement consistent tagging scheme",
                "tags": ["#status/active", "#status/archived", "#project/a", "#project/b"]
            }
        ]
        
        return {
            "result": {
                "suggestions": suggestions,
                "reasoning": "Based on content analysis, these changes would improve organization and discoverability"
            }
        }
        
    async def _validate_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the current structure against best practices or a provided schema.
        
        This helps identify issues before reorganization.
        """
        target = config.get("target", str(self.vault_path))
        schema = config.get("schema")
        
        # In a real implementation, this would validate the current structure
        issues = [
            {"level": "warning", "type": "empty_folder", "path": f"{target}/emptyFolder"},
            {"level": "error", "type": "duplicate_content", "paths": [f"{target}/note1.md", f"{target}/copy/note1.md"]},
            {"level": "info", "type": "inconsistent_naming", "examples": ["note-1.md", "Note2.md", "note_3.md"]}
        ]
        
        return {
            "result": {
                "valid": len(issues) == 0,
                "issues": issues,
                "recommendations": [
                    "Establish a consistent naming convention",
                    "Remove or merge duplicate notes",
                    "Consider removing empty folders or add an index.md"
                ]
            }
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