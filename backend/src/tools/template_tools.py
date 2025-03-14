from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
from ..services.content.templates import TemplateManager
from pathlib import Path
from datetime import datetime
import asyncio
from smolagents import Tool

class TemplateManagerTool(BaseTool):
    """Template management tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the template manager tool."""
        super().__init__()
        self.vault_path = vault_path
        self.template_manager = TemplateManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "template_manager"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Comprehensive template management for Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["create", "update", "delete", "list", "get", "apply", "validate"],
                "required": True
            },
            "name": {
                "type": "string",
                "description": "Template name",
                "required": False
            },
            "content": {
                "type": "string",
                "description": "Template content for create/update operations",
                "required": False
            },
            "variables": {
                "type": "object",
                "description": "Variables for template application",
                "required": False
            },
            "target_path": {
                "type": "string",
                "description": "Target path for apply operation",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the template management operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        action = parameters["action"]
        
        try:
            # Initialize service if needed
            if not self.template_manager.is_running:
                await self.template_manager.start()
                
            # Execute requested action
            if action == "create":
                return await self._create_template(parameters)
            elif action == "update":
                return await self._update_template(parameters)
            elif action == "delete":
                return await self._delete_template(parameters)
            elif action == "list":
                return await self._list_templates()
            elif action == "get":
                return await self._get_template(parameters)
            elif action == "apply":
                return await self._apply_template(parameters)
            elif action == "validate":
                return await self._validate_template(parameters)
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Template operation failed: {str(e)}")
            raise
            
    async def _create_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        name = parameters.get("name")
        content = parameters.get("content", "")
        
        if not name:
            raise ValueError("Name is required for create operation")
            
        await self.template_manager.create_template(name, content)
        return {
            "message": f"Created template {name}",
            "name": name,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _update_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing template."""
        name = parameters.get("name")
        content = parameters.get("content")
        
        if not name or content is None:
            raise ValueError("Name and content are required for update operation")
            
        await self.template_manager.update_template(name, content)
        return {
            "message": f"Updated template {name}",
            "name": name,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _delete_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a template."""
        name = parameters.get("name")
        if not name:
            raise ValueError("Name is required for delete operation")
            
        await self.template_manager.delete_template(name)
        return {
            "message": f"Deleted template {name}",
            "name": name,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _list_templates(self) -> Dict[str, Any]:
        """List all available templates."""
        templates = await self.template_manager.list_templates()
        return {
            "templates": templates,
            "count": len(templates),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get a template's content."""
        name = parameters.get("name")
        if not name:
            raise ValueError("Name is required for get operation")
            
        content = await self.template_manager.get_template(name)
        return {
            "name": name,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _apply_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a template to create a new note."""
        name = parameters.get("name")
        variables = parameters.get("variables", {})
        target_path = parameters.get("target_path")
        
        if not name or not target_path:
            raise ValueError("Name and target_path are required for apply operation")
            
        await self.template_manager.apply_template(name, target_path, variables)
        return {
            "message": f"Applied template {name} to {target_path}",
            "name": name,
            "target_path": target_path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _validate_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a template's syntax."""
        name = parameters.get("name")
        if not name:
            raise ValueError("Name is required for validate operation")
            
        validation_result = await self.template_manager.validate_template(name)
        return {
            "name": name,
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors if not validation_result.is_valid else [],
            "timestamp": datetime.now().isoformat()
        }

class DeleteTemplateTool(BaseTool):
    """Template deletion tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the template deletion tool."""
        super().__init__()
        self.vault_path = vault_path
        self.template_manager = TemplateManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "delete_template"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Delete a template from the vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "name": {
                "type": "string",
                "description": "The name of the template to delete",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "Optional folder path where the template is located",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the template deletion operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        name = parameters.get("name")
        folder = parameters.get("folder")
        
        try:
            # Initialize service if needed
            if not self.template_manager.is_running:
                await self.template_manager.start()
                
            # Get templates folder path
            templates_folder = Path(self.vault_path) / '.templates'
            if folder:
                templates_folder = templates_folder / folder
                
            # Get template file path
            file_path = templates_folder / f"{name}.md"
            
            # Check if template exists
            if not file_path.exists():
                raise ResourceNotFoundError(f"Template '{name}' not found")
                
            # Delete the template
            await self.template_manager.delete_template(name, folder)
            
            return {
                "message": f"Deleted template {name}",
                "name": name,
                "path": str(file_path.relative_to(self.vault_path)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Template deletion failed: {str(e)}")
            raise

class ListTemplatesTool(BaseTool):
    """Template listing tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the template listing tool."""
        super().__init__()
        self.vault_path = vault_path
        self.template_manager = TemplateManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "list_templates"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "List all templates in the vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "folder": {
                "type": "string",
                "description": "Optional folder path to list templates from",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the template listing operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        folder = parameters.get("folder")
        
        try:
            # Initialize service if needed
            if not self.template_manager.is_running:
                await self.template_manager.start()
                
            # Get templates folder path
            templates_folder = Path(self.vault_path) / '.templates'
            if folder:
                templates_folder = templates_folder / folder
                
            # List all template files
            templates = []
            for file_path in templates_folder.rglob("*.md"):
                templates.append({
                    "name": file_path.stem,
                    "path": str(file_path.relative_to(self.vault_path)),
                    "folder": str(file_path.parent.relative_to(templates_folder)) if folder else None
                })
                
            return {
                "templates": templates,
                "count": len(templates),
                "folder": folder,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Template listing failed: {str(e)}")
            raise

class ApplyTemplateTool(BaseTool):
    """Template application tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the template application tool."""
        super().__init__()
        self.vault_path = vault_path
        self.template_manager = TemplateManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "apply_template"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Apply a template to create or update a note"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "template_name": {
                "type": "string",
                "description": "Name of the template to apply",
                "required": True
            },
            "target_path": {
                "type": "string",
                "description": "Path where to create/update the note",
                "required": True
            },
            "variables": {
                "type": "object",
                "description": "Variables to use in template rendering",
                "required": False
            },
            "folder": {
                "type": "string",
                "description": "Optional folder path where the template is located",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the template application operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        template_name = parameters.get("template_name")
        target_path = parameters.get("target_path")
        variables = parameters.get("variables", {})
        folder = parameters.get("folder")
        
        try:
            # Initialize service if needed
            if not self.template_manager.is_running:
                await self.template_manager.start()
                
            # Apply template
            result = await self.template_manager.apply_template(
                template_name,
                target_path,
                variables,
                folder=folder
            )
            
            return {
                "message": f"Applied template {template_name} to {target_path}",
                "template_name": template_name,
                "target_path": target_path,
                "variables_used": list(variables.keys()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Template application failed: {str(e)}")
            raise

class GetTemplateContentTool(BaseTool):
    """Template content retrieval tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the template content tool."""
        super().__init__()
        self.vault_path = vault_path
        self.template_manager = TemplateManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "get_template_content"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Get the content of a specific template"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "name": {
                "type": "string",
                "description": "The name of the template",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "Optional folder path where the template is located",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the template content retrieval operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        name = parameters.get("name")
        folder = parameters.get("folder")
        
        try:
            # Initialize service if needed
            if not self.template_manager.is_running:
                await self.template_manager.start()
                
            # Get templates folder path
            templates_folder = Path(self.vault_path) / '.templates'
            if folder:
                templates_folder = templates_folder / folder
                
            # Get template file path
            file_path = templates_folder / f"{name}.md"
            
            # Check if template exists
            if not file_path.exists():
                raise ResourceNotFoundError(f"Template '{name}' not found")
                
            # Read template content
            content = await self.template_manager.get_template_content(name, folder)
            
            return {
                "name": name,
                "content": content,
                "path": str(file_path.relative_to(self.vault_path)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Template content retrieval failed: {str(e)}")
            raise

class TemplateEnforcementTool(BaseTool):
    """Template enforcement tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the template enforcement tool."""
        super().__init__()
        self.vault_path = vault_path
        self.template_manager = TemplateManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "template_enforcement"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Enforce template structure on notes and perform template audits"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["validate", "audit", "fix"],
                "required": True
            },
            "path": {
                "type": "string",
                "description": "The path to the note or folder to process",
                "required": False
            },
            "auto_fix": {
                "type": "boolean",
                "description": "Whether to automatically fix template issues when possible",
                "default": False,
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the template enforcement operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        action = parameters["action"]
        
        try:
            # Initialize service if needed
            if not self.template_manager.is_running:
                await self.template_manager.start()
                
            # Execute requested action
            if action == "validate":
                return await self._validate_note(parameters)
            elif action == "audit":
                return await self._audit_vault(parameters)
            elif action == "fix":
                return await self._fix_template_issues(parameters)
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Template enforcement failed: {str(e)}")
            raise
            
    async def _validate_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a note against its template."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for validate operation")
            
        try:
            # Get note content
            file_path = Path(self.vault_path) / path
            content = file_path.read_text()
            
            # Get note type from frontmatter or path
            note_type = await self._get_note_type(content, path)
            
            # Get template
            template_path = Path(self.vault_path) / ".templates" / f"{note_type[1:]}.md"
            if not template_path.exists():
                return {
                    "is_valid": False,
                    "message": f"Template not found for note type: {note_type}",
                    "note_type": note_type,
                    "timestamp": datetime.now().isoformat()
                }
                
            # Read template
            template_content = template_path.read_text()
            
            # Validate structure
            validation_result = await self._validate_structure(content, template_content)
            
            return {
                "is_valid": validation_result["is_valid"],
                "validation_errors": validation_result["validation_errors"],
                "structure_errors": validation_result["structure_errors"],
                "note_type": note_type,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise ToolError(f"Error validating note: {str(e)}")
            
    async def _audit_vault(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Audit vault or folder for template compliance."""
        path = parameters.get("path")
        
        try:
            # Get folder to audit
            audit_path = Path(self.vault_path)
            if path:
                audit_path = audit_path / path
                
            # Find all markdown files
            md_files = list(audit_path.rglob("*.md"))
            
            # Validate each file
            audit_results = []
            for file_path in md_files:
                rel_path = file_path.relative_to(self.vault_path)
                validation_result = await self._validate_note({"path": str(rel_path)})
                
                if not validation_result["is_valid"]:
                    audit_results.append({
                        "path": str(rel_path),
                        "validation_errors": validation_result["validation_errors"],
                        "structure_errors": validation_result["structure_errors"],
                        "note_type": validation_result["note_type"]
                    })
                    
            return {
                "total_files": len(md_files),
                "files_with_issues": len(audit_results),
                "audit_results": audit_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise ToolError(f"Error auditing vault: {str(e)}")
            
    async def _fix_template_issues(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fix template issues in a note."""
        path = parameters.get("path")
        auto_fix = parameters.get("auto_fix", False)
        
        if not path:
            raise ValueError("Path is required for fix operation")
            
        try:
            # Validate note first
            validation_result = await self._validate_note({"path": path})
            if validation_result["is_valid"]:
                return {
                    "message": "No issues found to fix",
                    "path": path,
                    "timestamp": datetime.now().isoformat()
                }
                
            # Get note content
            file_path = Path(self.vault_path) / path
            content = file_path.read_text()
            
            # Get template
            note_type = validation_result["note_type"]
            template_path = Path(self.vault_path) / ".templates" / f"{note_type[1:]}.md"
            template_content = template_path.read_text()
            
            # Fix structure
            fixed_content = await self._fix_structure(content, template_content)
            
            # Update note if auto_fix is enabled
            if auto_fix:
                file_path.write_text(fixed_content)
                
            return {
                "message": "Template issues fixed" if auto_fix else "Template issues identified",
                "path": path,
                "fixed_content": None if auto_fix else fixed_content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise ToolError(f"Error fixing template issues: {str(e)}")
            
    async def _get_note_type(self, content: str, path: str) -> str:
        """Get note type from frontmatter or path."""
        try:
            # Try to get from frontmatter
            frontmatter = await self.template_manager.get_frontmatter(content)
            note_type = frontmatter.get("note_type")
            if note_type:
                return f"#{note_type}"
                
            # Try to determine from path or filename
            filename = Path(path).name
            for tag in ["Category", "Document", "Note", "Code", "Log", "Main", "Person", "Mail"]:
                if f"#{tag}" in filename:
                    return f"#{tag}"
                    
            return "#Note"  # Default type
        except Exception as e:
            raise ToolError(f"Error getting note type: {str(e)}")
            
    async def _validate_structure(self, content: str, template_content: str) -> Dict[str, Any]:
        """Validate note structure against template."""
        try:
            # Get frontmatter
            note_frontmatter = await self.template_manager.get_frontmatter(content)
            template_frontmatter = await self.template_manager.get_frontmatter(template_content)
            
            # Validate frontmatter
            validation_errors = []
            for key, value in template_frontmatter.items():
                if key not in note_frontmatter:
                    validation_errors.append(f"Missing required frontmatter field: {key}")
                elif isinstance(value, list) and not isinstance(note_frontmatter[key], list):
                    validation_errors.append(f"Invalid type for {key}: expected list")
                    
            # Get sections
            note_sections = await self._extract_sections(content)
            template_sections = await self._extract_sections(template_content)
            
            # Validate sections
            structure_errors = []
            for section in template_sections:
                if section not in note_sections:
                    structure_errors.append(f"Missing required section: {section}")
                    
            return {
                "is_valid": len(validation_errors) == 0 and len(structure_errors) == 0,
                "validation_errors": validation_errors,
                "structure_errors": structure_errors
            }
        except Exception as e:
            raise ToolError(f"Error validating structure: {str(e)}")
            
    async def _fix_structure(self, content: str, template_content: str) -> str:
        """Fix note structure based on template."""
        try:
            # Get frontmatter
            note_frontmatter = await self.template_manager.get_frontmatter(content)
            template_frontmatter = await self.template_manager.get_frontmatter(template_content)
            
            # Fix frontmatter
            fixed_frontmatter = note_frontmatter.copy()
            for key, value in template_frontmatter.items():
                if key not in fixed_frontmatter:
                    if isinstance(value, list):
                        fixed_frontmatter[key] = []
                    elif isinstance(value, str):
                        fixed_frontmatter[key] = ""
                    elif isinstance(value, bool):
                        fixed_frontmatter[key] = False
                    elif isinstance(value, int):
                        fixed_frontmatter[key] = 0
                        
            # Update content with fixed frontmatter
            fixed_content = await self.template_manager.update_frontmatter(content, fixed_frontmatter)
            
            # Get sections
            note_sections = await self._extract_sections(fixed_content)
            template_sections = await self._extract_sections(template_content)
            
            # Add missing sections
            for section in template_sections:
                if section not in note_sections:
                    fixed_content += f"\n\n## {section}\n\n"
                    
            return fixed_content
        except Exception as e:
            raise ToolError(f"Error fixing structure: {str(e)}")
            
    async def _extract_sections(self, content: str) -> List[str]:
        """Extract section headers from content."""
        try:
            sections = []
            for line in content.split('\n'):
                if line.startswith('## '):
                    sections.append(line[3:].strip())
            return sections
        except Exception as e:
            raise ToolError(f"Error extracting sections: {str(e)}") 