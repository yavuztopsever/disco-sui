from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import jinja2
import os

class CreateTemplateTool(BaseTool):
    name = "create_template"
    description = "Create a new template in the vault"
    inputs = {
        "name": {
            "type": "string",
            "description": "The name of the template"
        },
        "content": {
            "type": "string",
            "description": "The content of the template"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where to create the template",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, name: str, content: str, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Validate and sanitize the name
            name = name.strip()
            if not name:
                raise ValueError("Template name cannot be empty")

            # Create templates folder path
            templates_folder = os.path.join(self.vault_path, '.templates')
            if folder:
                templates_folder = os.path.join(templates_folder, folder)
            self._ensure_path_exists(templates_folder)

            # Create the template file path
            file_path = os.path.join(templates_folder, f"{name}.md")

            # Write the template
            self._write_file(file_path, content)

            return {
                "success": True,
                "message": f"Template '{name}' created successfully",
                "path": os.path.relpath(file_path, self.vault_path)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create template: {str(e)}",
                "error": str(e)
            }

class DeleteTemplateTool(BaseTool):
    name = "delete_template"
    description = "Delete a template from the vault"
    inputs = {
        "name": {
            "type": "string",
            "description": "The name of the template to delete"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where the template is located",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, name: str, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get templates folder path
            templates_folder = os.path.join(self.vault_path, '.templates')
            if folder:
                templates_folder = os.path.join(templates_folder, folder)

            # Get template file path
            file_path = os.path.join(templates_folder, f"{name}.md")

            # Check if template exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Template '{name}' not found")

            # Delete the template
            os.remove(file_path)

            return {
                "success": True,
                "message": f"Template '{name}' deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete template: {str(e)}",
                "error": str(e)
            }

class ListTemplatesTool(BaseTool):
    name = "list_templates"
    description = "List all templates in the vault"
    inputs = {
        "folder": {
            "type": "string",
            "description": "Optional folder path to list templates from",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get templates folder path
            templates_folder = os.path.join(self.vault_path, '.templates')
            if folder:
                templates_folder = os.path.join(templates_folder, folder)

            # List all template files
            templates = []
            for root, _, files in os.walk(templates_folder):
                for file in files:
                    if file.endswith('.md'):
                        rel_path = os.path.relpath(os.path.join(root, file), templates_folder)
                        templates.append(rel_path)

            return {
                "success": True,
                "templates": templates
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list templates: {str(e)}",
                "error": str(e)
            }

class ApplyTemplateTool(BaseTool):
    name = "apply_template"
    description = "Apply a template to create a new note"
    inputs = {
        "template_name": {
            "type": "string",
            "description": "The name of the template to apply"
        },
        "title": {
            "type": "string",
            "description": "The title for the new note"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where to create the note",
            "nullable": True
        },
        "context": {
            "type": "object",
            "description": "Optional context data for template variables",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, template_name: str, title: str, folder: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get templates folder path
            templates_folder = os.path.join(self.vault_path, '.templates')
            template_path = os.path.join(templates_folder, f"{template_name}.md")

            # Check if template exists
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template '{template_name}' not found")

            # Read template content
            template_content = self._read_file(template_path)

            # Create Jinja2 environment
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(templates_folder),
                autoescape=True
            )

            # Load and render template
            template = env.from_string(template_content)
            rendered_content = template.render(**(context or {}))

            # Create note from template
            note_folder = self._get_full_path(folder) if folder else self.vault_path
            self._ensure_path_exists(note_folder)

            note_path = os.path.join(note_folder, f"{title}.md")
            self._write_file(note_path, rendered_content)

            return {
                "success": True,
                "message": f"Template '{template_name}' applied to create note '{title}' successfully",
                "path": os.path.relpath(note_path, self.vault_path)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to apply template: {str(e)}",
                "error": str(e)
            }

class GetTemplateContentTool(BaseTool):
    name = "get_template_content"
    description = "Get the content of a specific template"
    inputs = {
        "name": {
            "type": "string",
            "description": "The name of the template"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where the template is located",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, name: str, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get templates folder path
            templates_folder = os.path.join(self.vault_path, '.templates')
            if folder:
                templates_folder = os.path.join(templates_folder, folder)

            # Get template file path
            file_path = os.path.join(templates_folder, f"{name}.md")

            # Check if template exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Template '{name}' not found")

            # Read template content
            content = self._read_file(file_path)

            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get template content: {str(e)}",
                "error": str(e)
            }

class TemplateEnforcementTool(BaseTool):
    name = "enforce_template"
    description = "Enforce template structure on notes and perform template audits"
    inputs = {
        "action": {
            "type": "string",
            "description": "The action to perform: 'validate', 'audit', or 'fix'",
            "enum": ["validate", "audit", "fix"]
        },
        "path": {
            "type": "string",
            "description": "The path to the note or folder to process",
            "nullable": True
        },
        "auto_fix": {
            "type": "boolean",
            "description": "Whether to automatically fix template issues when possible",
            "default": False
        }
    }
    output_type = "object"

    def forward(self, action: str, path: Optional[str] = None, auto_fix: bool = False) -> Dict[str, Any]:
        try:
            if action == "validate":
                return self._validate_note(path)
            elif action == "audit":
                return self._audit_vault(path)
            elif action == "fix":
                return self._fix_template_issues(path, auto_fix)
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to enforce template: {str(e)}",
                "error": str(e)
            }

    def _validate_note(self, path: str) -> Dict[str, Any]:
        """Validate a single note against its template."""
        try:
            # Get note content
            content = self._read_file(path)
            frontmatter = self._get_frontmatter(content)
            
            # Determine note type from frontmatter or path
            note_type = frontmatter.get("node_type", "")
            if not note_type:
                # Try to determine from path or filename
                filename = os.path.basename(path)
                if any(tag in filename for tag in ["#Category", "#Document", "#Note", "#Code", "#Log", "#Main", "#Person", "#Mail"]):
                    note_type = next(tag for tag in ["#Category", "#Document", "#Note", "#Code", "#Log", "#Main", "#Person", "#Mail"] if tag in filename)
                else:
                    note_type = "#Note"  # Default type

            # Get template for note type
            template_path = os.path.join(self.vault_path, ".templates", f"{note_type[1:]}.md")
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "message": f"Template not found for note type: {note_type}",
                    "note_type": note_type
                }

            # Read template
            template_content = self._read_file(template_path)
            template_frontmatter = self._get_frontmatter(template_content)

            # Validate frontmatter
            validation_errors = []
            for key, value in template_frontmatter.items():
                if key not in frontmatter:
                    validation_errors.append(f"Missing required frontmatter field: {key}")
                elif isinstance(value, list) and not isinstance(frontmatter[key], list):
                    validation_errors.append(f"Invalid type for {key}: expected list")

            # Validate structure
            structure_errors = []
            template_sections = self._extract_sections(template_content)
            note_sections = self._extract_sections(content)
            
            for section in template_sections:
                if section not in note_sections:
                    structure_errors.append(f"Missing required section: {section}")

            return {
                "success": True,
                "valid": len(validation_errors) == 0 and len(structure_errors) == 0,
                "validation_errors": validation_errors,
                "structure_errors": structure_errors,
                "note_type": note_type
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to validate note: {str(e)}",
                "error": str(e)
            }

    def _audit_vault(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Perform a comprehensive audit of the vault or specified folder."""
        try:
            # Get folder to audit
            audit_path = self._get_full_path(path) if path else self.vault_path
            
            # Find all markdown files
            md_files = []
            for root, _, files in os.walk(audit_path):
                for file in files:
                    if file.endswith('.md'):
                        md_files.append(os.path.join(root, file))

            # Validate each file
            audit_results = []
            for file_path in md_files:
                result = self._validate_note(file_path)
                if not result["valid"]:
                    audit_results.append({
                        "path": os.path.relpath(file_path, self.vault_path),
                        "errors": result.get("validation_errors", []),
                        "structure_errors": result.get("structure_errors", [])
                    })

            return {
                "success": True,
                "total_files": len(md_files),
                "files_with_issues": len(audit_results),
                "audit_results": audit_results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to audit vault: {str(e)}",
                "error": str(e)
            }

    def _fix_template_issues(self, path: str, auto_fix: bool = False) -> Dict[str, Any]:
        """Fix template issues in a note."""
        try:
            # Validate note first
            validation_result = self._validate_note(path)
            if validation_result["valid"]:
                return {
                    "success": True,
                    "message": "No issues found to fix"
                }

            # Get note content
            content = self._read_file(path)
            frontmatter = self._get_frontmatter(content)
            
            # Get template
            note_type = validation_result["note_type"]
            template_path = os.path.join(self.vault_path, ".templates", f"{note_type[1:]}.md")
            template_content = self._read_file(template_path)
            template_frontmatter = self._get_frontmatter(template_content)

            # Fix frontmatter
            fixed_frontmatter = frontmatter.copy()
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

            # Fix structure
            fixed_content = content
            template_sections = self._extract_sections(template_content)
            note_sections = self._extract_sections(content)
            
            for section in template_sections:
                if section not in note_sections:
                    fixed_content += f"\n\n## {section}\n\n"

            # Update note
            if auto_fix:
                self._write_file(path, self._update_frontmatter(fixed_content, fixed_frontmatter))

            return {
                "success": True,
                "message": "Template issues identified and fixed" if auto_fix else "Template issues identified",
                "fixed_frontmatter": fixed_frontmatter,
                "fixed_content": fixed_content if not auto_fix else None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to fix template issues: {str(e)}",
                "error": str(e)
            }

    def _extract_sections(self, content: str) -> List[str]:
        """Extract section headers from content."""
        sections = []
        for line in content.split('\n'):
            if line.startswith('## '):
                sections.append(line[3:].strip())
        return sections 