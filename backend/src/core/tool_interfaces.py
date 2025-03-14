from typing import List, Dict, Any, Optional, Protocol, Union, Type, Callable, Awaitable
from pathlib import Path
from pydantic import BaseModel
from .text_processing import TextProcessor, ChunkingConfig
from .note_manipulation import NoteManipulator
from .semantic_analysis import SemanticAnalyzer
from .email_processing import EmailProcessor
from .base_interfaces import BaseInterface, ServiceInterface
from abc import ABC, abstractmethod
from datetime import datetime
import json
import asyncio
from smolagents import Tool

class ToolResponse(BaseModel):
    """Standard response model for tools."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class BaseTool(BaseInterface):
    """Base interface for all tools."""
    
    def __init__(self, service_manager):
        self.service_manager = service_manager
        
    @abstractmethod
    async def forward(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool's main functionality."""
        pass
        
    async def _get_service(self, name: str) -> Optional[ServiceInterface]:
        """Get a service by name."""
        return await self.service_manager.get_service(name)

class ContentTool(BaseTool):
    """Base interface for content manipulation tools."""
    
    async def process_content(
        self,
        content: str,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process content using the content processor service."""
        processor = await self._get_service("content_processor")
        if not processor:
            raise ValueError("Content processor service not available")
        return await processor.process_content(content, operation, **kwargs)

class StorageTool(BaseTool):
    """Base interface for storage manipulation tools."""
    
    async def read_file(self, path: Path) -> str:
        """Read file using storage service."""
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
        return await storage.read(path)
        
    async def write_file(self, path: Path, content: str) -> None:
        """Write file using storage service."""
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
        await storage.write(path, content)
        
    async def delete_file(self, path: Path) -> None:
        """Delete file using storage service."""
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
        await storage.delete(path)
        
    async def move_file(self, source: Path, target: Path) -> None:
        """Move file using storage service."""
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
        await storage.move(source, target)
        
    async def copy_file(self, source: Path, target: Path) -> None:
        """Copy file using storage service."""
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
        await storage.copy(source, target)
        
    async def list_files(
        self,
        directory: Optional[Path] = None,
        pattern: str = "*.md"
    ) -> List[Path]:
        """List files using storage service."""
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
        return await storage.list_files(directory, pattern)

class NoteTool(ContentTool, StorageTool):
    """Base interface for note manipulation tools."""
    
    async def create_note(
        self,
        title: str,
        content: str = "",
        template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new note."""
        # Process content if needed
        if template:
            result = await self.process_content(
                content,
                operation="transform",
                format="markdown",
                templates={"template": template}
            )
            content = result["content"]
            
        # Generate path and write
        path = Path(f"{title}.md")
        await self.write_file(path, content)
        
        return {
            "success": True,
            "note_path": str(path)
        }
        
    async def update_note(
        self,
        path: Path,
        content: Optional[str] = None,
        search: Optional[str] = None,
        replace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a note's content."""
        if content is not None:
            await self.write_file(path, content)
            return {
                "success": True,
                "note_path": str(path),
                "update_type": "full"
            }
            
        if search is not None and replace is not None:
            current = await self.read_file(path)
            result = await self.process_content(
                current,
                operation="transform",
                search=search,
                replace=replace
            )
            await self.write_file(path, result["content"])
            return {
                "success": True,
                "note_path": str(path),
                "update_type": "replace",
                "replacements": result.get("replacements", 0)
            }
            
        raise ValueError("Either content or search/replace must be provided")
        
    async def delete_note(self, path: Path) -> Dict[str, Any]:
        """Delete a note."""
        await self.delete_file(path)
        return {
            "success": True,
            "note_path": str(path)
        }
        
    async def move_note(
        self,
        source: Path,
        target: Path
    ) -> Dict[str, Any]:
        """Move a note to a new location."""
        await self.move_file(source, target)
        return {
            "success": True,
            "source": str(source),
            "target": str(target)
        }
        
    async def search_notes(
        self,
        query: str,
        directory: Optional[Path] = None,
        pattern: str = "*.md"
    ) -> List[Dict[str, Any]]:
        """Search notes for content."""
        results = []
        for path in await self.list_files(directory, pattern):
            try:
                content = await self.read_file(path)
                if query.lower() in content.lower():
                    results.append({
                        "path": str(path),
                        "matches": content.lower().count(query.lower())
                    })
            except Exception as e:
                continue
        return sorted(results, key=lambda x: x["matches"], reverse=True)

class OrganizationTool(StorageTool):
    """Base interface for organization tools."""
    
    async def analyze_structure(
        self,
        directory: Optional[Path] = None,
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """Analyze directory structure."""
        files = await self.list_files(directory, pattern)
        
        stats = {
            "total_files": len(files),
            "file_types": {},
            "directories": set()
        }
        
        for file in files:
            # Count file types
            ext = file.suffix
            stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
            
            # Track directories
            stats["directories"].add(str(file.parent))
            
        stats["total_directories"] = len(stats["directories"])
        return stats
        
    async def reorganize(
        self,
        rules: Dict[str, Any],
        directory: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Reorganize content based on rules."""
        changes = {
            "moved": [],
            "created_dirs": set(),
            "errors": []
        }
        
        try:
            files = await self.list_files(directory)
            
            for file in files:
                try:
                    # Apply rules
                    if "type_dirs" in rules:
                        ext = file.suffix
                        if ext in rules["type_dirs"]:
                            target_dir = Path(rules["type_dirs"][ext])
                            target = target_dir / file.name
                            await self.move_file(file, target)
                            changes["moved"].append({
                                "source": str(file),
                                "target": str(target)
                            })
                            changes["created_dirs"].add(str(target_dir))
                except Exception as e:
                    changes["errors"].append({
                        "file": str(file),
                        "error": str(e)
                    })
                    
        except Exception as e:
            changes["errors"].append({
                "general": str(e)
            })
            
        return changes

class ContentToolInterface(BaseToolInterface):
    """Interface for content manipulation tools."""
    
    async def chunk_content(
        self,
        content: str,
        config: Optional[ChunkingConfig] = None
    ) -> ToolResponse:
        """Chunk content using the text processor."""
        try:
            chunks = self.text_processor.chunk_content(
                content,
                config or ChunkingConfig()
            )
            return ToolResponse(
                success=True,
                result={"chunks": chunks}
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e)
            )

class NoteToolInterface(BaseToolInterface):
    """Interface for note manipulation tools."""
    
    async def merge_notes(
        self,
        source_paths: List[str],
        target_path: str,
        merge_strategy: str = "append"
    ) -> ToolResponse:
        """Merge notes using the note manipulator."""
        try:
            result = await self.note_manipulator.merge_notes(
                [Path(p) for p in source_paths],
                Path(target_path),
                merge_strategy
            )
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def split_note(
        self,
        source_path: str,
        split_criteria: str = "heading"
    ) -> ToolResponse:
        """Split a note using the note manipulator."""
        try:
            result = await self.note_manipulator.split_note(
                Path(source_path),
                split_criteria
            )
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

class SemanticToolInterface(BaseToolInterface):
    """Interface for semantic analysis tools."""
    
    async def analyze_note(self, note_path: str) -> ToolResponse:
        """Analyze a note using the semantic analyzer."""
        try:
            result = await self.semantic_analyzer.analyze_note(Path(note_path))
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def find_related_notes(
        self,
        note_path: str,
        max_related: int = 5,
        min_similarity: float = 0.5
    ) -> ToolResponse:
        """Find related notes using the semantic analyzer."""
        try:
            result = await self.semantic_analyzer.find_related_notes(
                Path(note_path),
                max_related,
                min_similarity
            )
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def generate_knowledge_graph(
        self,
        include_hierarchy: bool = True,
        include_semantic: bool = True
    ) -> ToolResponse:
        """Generate a knowledge graph using the semantic analyzer."""
        try:
            result = await self.semantic_analyzer.generate_knowledge_graph(
                include_hierarchy,
                include_semantic
            )
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

class EmailToolInterface(BaseToolInterface):
    """Interface for email processing tools."""
    
    async def process_email(self, email_path: str) -> ToolResponse:
        """Process an email using the email processor."""
        try:
            result = await self.email_processor.process_email(Path(email_path))
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def search_emails(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        date_range: Optional[tuple[str, str]] = None
    ) -> ToolResponse:
        """Search emails using the email processor."""
        try:
            # Convert date strings to datetime if provided
            date_tuple = None
            if date_range:
                from datetime import datetime
                date_tuple = (
                    datetime.fromisoformat(date_range[0]),
                    datetime.fromisoformat(date_range[1])
                )
            
            result = await self.email_processor.search_emails(
                query,
                categories,
                date_tuple
            )
            return ToolResponse(success=True, result={"matches": result})
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def update_categories(
        self,
        note_path: str,
        categories: List[str]
    ) -> ToolResponse:
        """Update email categories using the email processor."""
        try:
            result = await self.email_processor.update_categories(
                Path(note_path),
                categories
            )
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def cleanup_old_emails(
        self,
        days: int = 30,
        dry_run: bool = True
    ) -> ToolResponse:
        """Clean up old emails using the email processor."""
        try:
            result = await self.email_processor.cleanup_old_emails(days, dry_run)
            return ToolResponse(success=True, result=result)
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

class AnalysisTool(BaseTool):
    """Base interface for analysis tools."""
    
    async def analyze_content(
        self,
        content: Union[str, Path],
        analysis_type: str = "semantic",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content using analysis service.
        
        Args:
            content: Content to analyze (string or file path)
            analysis_type: Type of analysis to perform
                - "semantic": Semantic analysis
                - "structure": Structure analysis
                - "metadata": Metadata analysis
                - "links": Link analysis
                - "tags": Tag analysis
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis results
        """
        analyzer = await self._get_service("content_analyzer")
        if not analyzer:
            raise ValueError("Analysis service not available")
            
        # If content is a path, read the file
        if isinstance(content, Path):
            storage = await self._get_service("vault_storage")
            if not storage:
                raise ValueError("Storage service not available")
            content = await storage.read(content)
            
        return await analyzer.analyze(content, analysis_type, **kwargs)
    
    async def find_related(
        self,
        source: Union[str, Path],
        max_results: int = 5,
        min_similarity: float = 0.5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Find related content.
        
        Args:
            source: Source content or path
            max_results: Maximum number of results
            min_similarity: Minimum similarity threshold
            **kwargs: Additional search parameters
            
        Returns:
            List of related items
        """
        analyzer = await self._get_service("content_analyzer")
        if not analyzer:
            raise ValueError("Analysis service not available")
            
        # If source is a path, read the file
        if isinstance(source, Path):
            storage = await self._get_service("vault_storage")
            if not storage:
                raise ValueError("Storage service not available")
            source = await storage.read(source)
            
        return await analyzer.find_related(
            source,
            max_results,
            min_similarity,
            **kwargs
        )
    
    async def generate_graph(
        self,
        include_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate knowledge graph.
        
        Args:
            include_types: Types of relationships to include
            **kwargs: Additional graph parameters
            
        Returns:
            Graph data
        """
        analyzer = await self._get_service("content_analyzer")
        if not analyzer:
            raise ValueError("Analysis service not available")
            
        return await analyzer.generate_graph(include_types, **kwargs)
    
    async def extract_metadata(
        self,
        content: Union[str, Path],
        metadata_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Extract metadata from content.
        
        Args:
            content: Content to analyze
            metadata_types: Types of metadata to extract
            **kwargs: Additional extraction parameters
            
        Returns:
            Extracted metadata
        """
        analyzer = await self._get_service("content_analyzer")
        if not analyzer:
            raise ValueError("Analysis service not available")
            
        # If content is a path, read the file
        if isinstance(content, Path):
            storage = await self._get_service("vault_storage")
            if not storage:
                raise ValueError("Storage service not available")
            content = await storage.read(content)
            
        return await analyzer.extract_metadata(content, metadata_types, **kwargs)

class TagTool(AnalysisTool):
    """Base interface for tag manipulation tools."""
    
    async def extract_tags(
        self,
        content: Union[str, Path],
        include_hierarchy: bool = True
    ) -> List[str]:
        """Extract tags from content.
        
        Args:
            content: Content to extract tags from
            include_hierarchy: Whether to include hierarchical tags
            
        Returns:
            List of extracted tags
        """
        metadata = await self.extract_metadata(
            content,
            metadata_types=["tags"],
            include_hierarchy=include_hierarchy
        )
        return metadata.get("tags", [])
    
    async def update_tags(
        self,
        path: Path,
        tags: List[str],
        operation: str = "add"
    ) -> Dict[str, Any]:
        """Update tags in a file.
        
        Args:
            path: Path to the file
            tags: Tags to update
            operation: Operation to perform ("add", "remove", "set")
            
        Returns:
            Update results
        """
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
            
        # Read current content
        content = await storage.read(path)
        
        # Get current tags
        current_tags = await self.extract_tags(content)
        
        # Update tags
        if operation == "add":
            new_tags = list(set(current_tags + tags))
        elif operation == "remove":
            new_tags = [t for t in current_tags if t not in tags]
        elif operation == "set":
            new_tags = tags
        else:
            raise ValueError(f"Invalid operation: {operation}")
            
        # Update content with new tags
        processor = await self._get_service("content_processor")
        if not processor:
            raise ValueError("Content processor service not available")
            
        result = await processor.process_content(
            content,
            operation="transform",
            update_tags=new_tags
        )
        
        # Write updated content
        await storage.write(path, result["content"])
        
        return {
            "success": True,
            "path": str(path),
            "previous_tags": current_tags,
            "new_tags": new_tags
        }

class TemplateTool(ContentTool):
    """Base interface for template manipulation tools."""
    
    async def apply_template(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Apply a template.
        
        Args:
            template_name: Name of the template
            variables: Template variables
            **kwargs: Additional template parameters
            
        Returns:
            Processed template
        """
        processor = await self._get_service("content_processor")
        if not processor:
            raise ValueError("Content processor service not available")
            
        return await processor.process_content(
            "",  # Empty content since we're using a template
            operation="transform",
            template=template_name,
            template_vars=variables,
            **kwargs
        )
    
    async def create_template(
        self,
        name: str,
        content: str,
        description: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a new template.
        
        Args:
            name: Template name
            content: Template content
            description: Template description
            variables: Template variable descriptions
            
        Returns:
            Creation results
        """
        storage = await self._get_service("vault_storage")
        if not storage:
            raise ValueError("Storage service not available")
            
        # Create template metadata
        metadata = {
            "name": name,
            "description": description or "",
            "variables": variables or {},
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
        
        # Write template
        template_path = Path(".templates") / f"{name}.md"
        await storage.write(template_path, content)
        
        # Write metadata
        metadata_path = Path(".templates") / f"{name}.json"
        await storage.write(metadata_path, json.dumps(metadata, indent=2))
        
        return {
            "success": True,
            "template": metadata
        }

class ServiceTool(BaseTool):
    """Base interface for service-based tools."""
    
    async def _get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get the status of a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service status information
        """
        service = await self._get_service(service_name)
        if not service:
            raise ValueError(f"Service not available: {service_name}")
        return await service.get_status()
    
    async def _start_service(self, service_name: str) -> None:
        """Start a service.
        
        Args:
            service_name: Name of the service
        """
        service = await self._get_service(service_name)
        if not service:
            raise ValueError(f"Service not available: {service_name}")
        await service.start()
    
    async def _stop_service(self, service_name: str) -> None:
        """Stop a service.
        
        Args:
            service_name: Name of the service
        """
        service = await self._get_service(service_name)
        if not service:
            raise ValueError(f"Service not available: {service_name}")
        await service.stop()
    
    async def _health_check(self, service_name: str) -> bool:
        """Check if a service is healthy.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if service is healthy
        """
        service = await self._get_service(service_name)
        if not service:
            raise ValueError(f"Service not available: {service_name}")
        return await service.health_check()
    
    async def _trigger_service_update(
        self,
        service_name: str,
        target_paths: Optional[List[Path]] = None,
        force_update: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Trigger a service update.
        
        Args:
            service_name: Name of the service
            target_paths: Optional list of paths to update
            force_update: Whether to force the update
            **kwargs: Additional update parameters
            
        Returns:
            Update results
        """
        service = await self._get_service(service_name)
        if not service:
            raise ValueError(f"Service not available: {service_name}")
        return await service.update(target_paths, force_update, **kwargs)

class FolderTool(Tool):
    """Base interface for folder management tools."""
    # ... existing code ...

class AudioTool(Tool):
    """Base interface for audio processing tools."""
    # ... existing code ...

class IndexingTool(Tool):
    """Base interface for indexing and search tools."""
    # ... existing code ...

class SemanticTool(Tool):
    """Base interface for semantic analysis tools."""
    # ... existing code ...

class OrganizationTool(Tool):
    """Base interface for organization tools."""
    # ... existing code ...

class ToolHierarchy:
    """Tool hierarchy configuration."""
    
    TOOL_TYPES = {
        "content": {
            "base": ContentTool,
            "children": {
                "note": NoteTool,
                "template": TemplateTool,
                "email": EmailToolInterface
            }
        },
        "analysis": {
            "base": AnalysisTool,
            "children": {
                "semantic": SemanticToolInterface,
                "indexing": IndexingToolInterface,
                "tag": TagTool
            }
        },
        "organization": {
            "base": OrganizationTool,
            "children": {
                "folder": FolderTool,
                "hierarchy": HierarchyTool
            }
        },
        "service": {
            "base": ServiceTool,
            "children": {
                "manager": ServiceManagerTool,
                "registry": ServiceRegistryTool
            }
        }
    }
    
    @classmethod
    def get_tool_type(cls, tool_class: type) -> Optional[str]:
        """Get the type of a tool class.
        
        Args:
            tool_class: Tool class to check
            
        Returns:
            Tool type if found
        """
        for type_name, type_info in cls.TOOL_TYPES.items():
            if issubclass(tool_class, type_info["base"]):
                return type_name
            for child_name, child_class in type_info["children"].items():
                if issubclass(tool_class, child_class):
                    return f"{type_name}.{child_name}"
        return None
    
    @classmethod
    def get_base_class(cls, tool_type: str) -> Optional[type]:
        """Get the base class for a tool type.
        
        Args:
            tool_type: Tool type to get base class for
            
        Returns:
            Base class if found
        """
        parts = tool_type.split(".")
        type_info = cls.TOOL_TYPES.get(parts[0])
        if not type_info:
            return None
            
        if len(parts) == 1:
            return type_info["base"]
            
        return type_info["children"].get(parts[1])
    
    @classmethod
    def get_child_types(cls, base_type: str) -> List[str]:
        """Get child types for a base type.
        
        Args:
            base_type: Base type to get children for
            
        Returns:
            List of child type names
        """
        type_info = cls.TOOL_TYPES.get(base_type)
        if not type_info:
            return []
            
        return list(type_info["children"].keys())
    
    @classmethod
    def validate_hierarchy(cls) -> List[str]:
        """Validate the tool hierarchy.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check base classes
        for type_name, type_info in cls.TOOL_TYPES.items():
            base_class = type_info["base"]
            if not issubclass(base_class, BaseTool):
                errors.append(f"Base class for {type_name} must inherit from BaseTool")
            
            # Check child classes
            for child_name, child_class in type_info["children"].items():
                if not issubclass(child_class, base_class):
                    errors.append(
                        f"Child class {child_name} must inherit from {base_class.__name__}"
                    )
        
        return errors

class ToolRegistry:
    """Registry for managing tool instances."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._hierarchy = ToolHierarchy()
        
    async def register_tool(
        self,
        name: str,
        tool: BaseTool,
        tool_type: Optional[str] = None
    ) -> None:
        """Register a tool.
        
        Args:
            name: Tool name
            tool: Tool instance
            tool_type: Optional tool type override
        """
        if tool_type is None:
            tool_type = self._hierarchy.get_tool_type(tool.__class__)
            if tool_type is None:
                raise ValueError(f"Could not determine type for tool {name}")
        
        self._tools[name] = tool
        
    async def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance if found
        """
        return self._tools.get(name)
        
    async def list_tools(self, tool_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered tools.
        
        Args:
            tool_type: Optional type to filter by
            
        Returns:
            List of tool information
        """
        tools = []
        for name, tool in self._tools.items():
            tool_info = {
                "name": name,
                "type": self._hierarchy.get_tool_type(tool.__class__),
                "description": tool.__doc__ or ""
            }
            
            if tool_type is None or tool_info["type"].startswith(tool_type):
                tools.append(tool_info)
                
        return tools
        
    async def get_tools_by_type(self, tool_type: str) -> List[BaseTool]:
        """Get all tools of a specific type.
        
        Args:
            tool_type: Tool type to filter by
            
        Returns:
            List of matching tools
        """
        return [
            tool for tool in self._tools.values()
            if self._hierarchy.get_tool_type(tool.__class__).startswith(tool_type)
        ]

class DependencyManager:
    """Manager for handling service and tool dependencies."""
    
    def __init__(self):
        self._service_registry = ServiceRegistry()
        self._tool_registry = ToolRegistry()
        self._dependency_graph = {}
        
    async def register_service(
        self,
        name: str,
        service: Any,
        dependencies: Optional[List[str]] = None,
        required_by: Optional[List[str]] = None
    ) -> None:
        """Register a service with dependencies.
        
        Args:
            name: Service name
            service: Service instance
            dependencies: Services this service depends on
            required_by: Services that require this service
        """
        await self._service_registry.register_service(name, service, dependencies)
        
        # Update dependency graph
        self._dependency_graph[f"service:{name}"] = {
            "dependencies": [f"service:{d}" for d in (dependencies or [])],
            "required_by": [f"service:{r}" for r in (required_by or [])]
        }
        
    async def register_tool(
        self,
        name: str,
        tool: BaseTool,
        tool_type: Optional[str] = None,
        service_dependencies: Optional[List[str]] = None,
        tool_dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a tool with dependencies.
        
        Args:
            name: Tool name
            tool: Tool instance
            tool_type: Optional tool type override
            service_dependencies: Services this tool depends on
            tool_dependencies: Tools this tool depends on
        """
        await self._tool_registry.register_tool(name, tool, tool_type)
        
        # Update dependency graph
        self._dependency_graph[f"tool:{name}"] = {
            "dependencies": [
                f"service:{d}" for d in (service_dependencies or [])
            ] + [
                f"tool:{d}" for d in (tool_dependencies or [])
            ],
            "required_by": []
        }
        
    async def start_required_services(self, tool_name: str) -> None:
        """Start all services required by a tool.
        
        Args:
            tool_name: Name of the tool
        """
        # Get all service dependencies
        services_to_start = set()
        queue = [f"tool:{tool_name}"]
        
        while queue:
            node = queue.pop(0)
            if node.startswith("service:"):
                services_to_start.add(node[8:])  # Remove "service:" prefix
            
            for dep in self._dependency_graph.get(node, {}).get("dependencies", []):
                if dep not in queue:
                    queue.append(dep)
        
        # Start services in dependency order
        for service_name in services_to_start:
            await self._service_registry.start_service(service_name)
            
    async def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance if found
        """
        return await self._service_registry.get_service(name)
        
    async def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance if found
        """
        return await self._tool_registry.get_tool(name)
        
    async def list_dependencies(
        self,
        name: str,
        include_tools: bool = True,
        include_services: bool = True
    ) -> Dict[str, List[str]]:
        """List dependencies for a tool or service.
        
        Args:
            name: Name of tool or service
            include_tools: Whether to include tool dependencies
            include_services: Whether to include service dependencies
            
        Returns:
            Dictionary of dependencies
        """
        prefix = "tool:" if ":" not in name else ""
        node = f"{prefix}{name}"
        
        if node not in self._dependency_graph:
            return {"tools": [], "services": []}
            
        deps = {"tools": [], "services": []}
        for dep in self._dependency_graph[node]["dependencies"]:
            if dep.startswith("tool:") and include_tools:
                deps["tools"].append(dep[5:])  # Remove "tool:" prefix
            elif dep.startswith("service:") and include_services:
                deps["services"].append(dep[8:])  # Remove "service:" prefix
                
        return deps
        
    async def validate_dependencies(self) -> List[str]:
        """Validate all dependencies.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for circular dependencies
        visited = set()
        path = []
        
        def check_circular(node: str) -> None:
            if node in path:
                cycle = path[path.index(node):] + [node]
                errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")
                return
                
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            
            for dep in self._dependency_graph.get(node, {}).get("dependencies", []):
                check_circular(dep)
                
            path.pop()
            
        for node in self._dependency_graph:
            check_circular(node)
            
        # Check for missing dependencies
        for node, info in self._dependency_graph.items():
            for dep in info["dependencies"]:
                if dep not in self._dependency_graph:
                    errors.append(f"Missing dependency {dep} required by {node}")
                    
        return errors 