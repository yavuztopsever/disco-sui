from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ToolDocumentation(BaseModel):
    """Model for tool documentation."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    inputs: Dict[str, Any] = Field(..., description="Input parameters and their types")
    output_type: str = Field(..., description="Type of the tool's output")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example usages")
    error_handling: Dict[str, Any] = Field(default_factory=dict, description="Error handling strategies")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies required by the tool")
    version: str = Field(default="1.0.0", description="Version of the tool")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")

class ToolDocumentationManager:
    """Manager for tool documentation and validation."""
    
    def __init__(self, docs_dir: str = "docs/tools"):
        """Initialize the documentation manager."""
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.documentation: Dict[str, ToolDocumentation] = {}
        self._load_documentation()

    def _load_documentation(self):
        """Load existing tool documentation."""
        try:
            for doc_file in self.docs_dir.glob("*.json"):
                try:
                    with open(doc_file, 'r') as f:
                        doc_data = json.load(f)
                        self.documentation[doc_data["name"]] = ToolDocumentation(**doc_data)
                except Exception as e:
                    logger.error(f"Failed to load documentation for {doc_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load tool documentation: {str(e)}")

    def save_documentation(self, tool_name: str, documentation: ToolDocumentation):
        """Save tool documentation to a JSON file."""
        try:
            doc_file = self.docs_dir / f"{tool_name}.json"
            with open(doc_file, 'w') as f:
                json.dump(documentation.dict(), f, indent=2)
            self.documentation[tool_name] = documentation
            logger.info(f"Saved documentation for tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to save documentation for {tool_name}: {str(e)}")
            raise

    def get_documentation(self, tool_name: str) -> Optional[ToolDocumentation]:
        """Get documentation for a specific tool."""
        return self.documentation.get(tool_name)

    def validate_tool(self, tool_name: str, tool_instance: Any) -> bool:
        """Validate a tool against its documentation."""
        try:
            doc = self.get_documentation(tool_name)
            if not doc:
                logger.warning(f"No documentation found for tool: {tool_name}")
                return False

            # Validate required attributes
            required_attrs = ['name', 'description', 'inputs', 'output_type']
            for attr in required_attrs:
                if not hasattr(tool_instance, attr):
                    logger.error(f"Tool {tool_name} missing required attribute: {attr}")
                    return False

            # Validate input schema
            if not isinstance(tool_instance.inputs, dict):
                logger.error(f"Tool {tool_name} inputs must be a dictionary")
                return False

            # Validate output type
            if not isinstance(tool_instance.output_type, str):
                logger.error(f"Tool {tool_name} output_type must be a string")
                return False

            # Validate against documentation
            if tool_instance.name != doc.name:
                logger.error(f"Tool name mismatch: {tool_instance.name} != {doc.name}")
                return False

            if tool_instance.description != doc.description:
                logger.error(f"Tool description mismatch for {tool_name}")
                return False

            if tool_instance.inputs != doc.inputs:
                logger.error(f"Tool inputs mismatch for {tool_name}")
                return False

            if tool_instance.output_type != doc.output_type:
                logger.error(f"Tool output_type mismatch for {tool_name}")
                return False

            return True
        except Exception as e:
            logger.error(f"Failed to validate tool {tool_name}: {str(e)}")
            return False

    def generate_documentation(self, tool_name: str, tool_instance: Any) -> ToolDocumentation:
        """Generate documentation for a tool."""
        try:
            doc = ToolDocumentation(
                name=tool_name,
                description=tool_instance.description,
                inputs=tool_instance.inputs,
                output_type=tool_instance.output_type,
                examples=getattr(tool_instance, 'examples', []),
                error_handling=getattr(tool_instance, 'error_handling', {}),
                dependencies=getattr(tool_instance, 'dependencies', []),
                version=getattr(tool_instance, 'version', '1.0.0')
            )
            self.save_documentation(tool_name, doc)
            return doc
        except Exception as e:
            logger.error(f"Failed to generate documentation for {tool_name}: {str(e)}")
            raise

    def update_documentation(self, tool_name: str, updates: Dict[str, Any]) -> ToolDocumentation:
        """Update documentation for a tool."""
        try:
            doc = self.get_documentation(tool_name)
            if not doc:
                raise ValueError(f"No documentation found for tool: {tool_name}")

            # Update fields
            for field, value in updates.items():
                if hasattr(doc, field):
                    setattr(doc, field, value)

            # Save updated documentation
            self.save_documentation(tool_name, doc)
            return doc
        except Exception as e:
            logger.error(f"Failed to update documentation for {tool_name}: {str(e)}")
            raise

    def get_all_tools(self) -> List[str]:
        """Get a list of all documented tools."""
        return list(self.documentation.keys())

    def get_tool_examples(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get examples for a specific tool."""
        doc = self.get_documentation(tool_name)
        return doc.examples if doc else []

    def get_tool_error_handling(self, tool_name: str) -> Dict[str, Any]:
        """Get error handling strategies for a specific tool."""
        doc = self.get_documentation(tool_name)
        return doc.error_handling if doc else {}

    def get_tool_dependencies(self, tool_name: str) -> List[str]:
        """Get dependencies for a specific tool."""
        doc = self.get_documentation(tool_name)
        return doc.dependencies if doc else [] 