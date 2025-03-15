from typing import Dict, List, Optional, Set, Union, Any
from pathlib import Path
from datetime import datetime
import re
from pydantic import BaseModel, Field
import networkx as nx
import yaml

from ..base_service import BaseService
from ...core.exceptions import OrganizationError

class TagInfo(BaseModel):
    """Model for tag information."""
    name: str
    count: int = 0
    last_used: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None
    parent_tags: List[str] = Field(default_factory=list)
    child_tags: List[str] = Field(default_factory=list)

class HierarchyNode(BaseModel):
    """Model for hierarchy node."""
    name: str
    type: str  # 'category', 'note', 'tag'
    children: List[str] = Field(default_factory=list)
    parents: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OrganizationConfig(BaseModel):
    """Configuration for organization service."""
    vault_path: Path
    tag_database_path: Path
    hierarchy_path: Path
    enforce_hierarchy: bool = True
    auto_tag: bool = True
    tag_prefix: str = "#"
    default_category: str = "Uncategorized"

class OrganizationService(BaseService):
    """Service for managing tags, hierarchies, and note organization."""

    def _initialize(self) -> None:
        """Initialize organization service configuration and resources."""
        self.config_model = OrganizationConfig(**self.config)
        self._tag_database: Dict[str, TagInfo] = {}
        self._hierarchy: nx.DiGraph = nx.DiGraph()
        self._ensure_directories()
        self._load_tag_database()
        self._load_hierarchy()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.config_model.tag_database_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_model.hierarchy_path.parent.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the organization service."""
        pass  # No background tasks needed

    async def stop(self) -> None:
        """Stop the organization service."""
        await self._save_tag_database()
        await self._save_hierarchy()

    async def health_check(self) -> bool:
        """Check if the organization service is healthy."""
        return (
            self.config_model.vault_path.exists() and
            bool(self._tag_database) and
            not nx.is_empty(self._hierarchy)
        )

    def _load_tag_database(self) -> None:
        """Load tag database from file."""
        try:
            if self.config_model.tag_database_path.exists():
                data = yaml.safe_load(self.config_model.tag_database_path.read_text())
                self._tag_database = {
                    name: TagInfo(**info) for name, info in data.items()
                }
        except Exception as e:
            raise OrganizationError(f"Failed to load tag database: {str(e)}")

    async def _save_tag_database(self) -> None:
        """Save tag database to file."""
        try:
            data = {
                name: tag.dict() for name, tag in self._tag_database.items()
            }
            self.config_model.tag_database_path.write_text(
                yaml.dump(data, default_flow_style=False)
            )
        except Exception as e:
            raise OrganizationError(f"Failed to save tag database: {str(e)}")

    def _load_hierarchy(self) -> None:
        """Load hierarchy from file."""
        try:
            if self.config_model.hierarchy_path.exists():
                data = yaml.safe_load(self.config_model.hierarchy_path.read_text())
                self._hierarchy.clear()
                
                # Add nodes
                for name, node_data in data.items():
                    node = HierarchyNode(**node_data)
                    self._hierarchy.add_node(name, **node.dict())
                
                # Add edges
                for name, node_data in data.items():
                    node = HierarchyNode(**node_data)
                    for child in node.children:
                        self._hierarchy.add_edge(name, child)
        except Exception as e:
            raise OrganizationError(f"Failed to load hierarchy: {str(e)}")

    async def _save_hierarchy(self) -> None:
        """Save hierarchy to file."""
        try:
            data = {}
            for node in self._hierarchy.nodes():
                node_data = self._hierarchy.nodes[node]
                data[node] = HierarchyNode(
                    name=node,
                    type=node_data["type"],
                    children=list(self._hierarchy.successors(node)),
                    parents=list(self._hierarchy.predecessors(node)),
                    metadata=node_data.get("metadata", {})
                ).dict()
            
            self.config_model.hierarchy_path.write_text(
                yaml.dump(data, default_flow_style=False)
            )
        except Exception as e:
            raise OrganizationError(f"Failed to save hierarchy: {str(e)}")

    async def extract_tags(self, content: str) -> Set[str]:
        """Extract tags from content."""
        pattern = rf"{re.escape(self.config_model.tag_prefix)}[\w/]+"
        return set(re.findall(pattern, content))

    async def update_tag_database(self, tags: Set[str]) -> None:
        """Update tag database with new tags."""
        for tag in tags:
            name = tag.lstrip(self.config_model.tag_prefix)
            if name not in self._tag_database:
                self._tag_database[name] = TagInfo(name=name)
            
            tag_info = self._tag_database[name]
            tag_info.count += 1
            tag_info.last_used = datetime.now()

        await self._save_tag_database()

    async def get_tag_info(self, tag: str) -> Optional[TagInfo]:
        """Get information about a tag."""
        name = tag.lstrip(self.config_model.tag_prefix)
        return self._tag_database.get(name)

    async def add_to_hierarchy(
        self,
        name: str,
        node_type: str,
        parent: Optional[str] = None,
        metadata: Optional[Dict[str, any]] = None
    ) -> None:
        """Add a node to the hierarchy."""
        try:
            if parent and parent not in self._hierarchy:
                raise OrganizationError(f"Parent node '{parent}' not found")

            self._hierarchy.add_node(
                name,
                type=node_type,
                metadata=metadata or {}
            )

            if parent:
                self._hierarchy.add_edge(parent, name)

            await self._save_hierarchy()

        except Exception as e:
            raise OrganizationError(f"Failed to add node to hierarchy: {str(e)}")

    async def get_node_hierarchy(self, name: str) -> Dict[str, any]:
        """Get hierarchy information for a node."""
        if name not in self._hierarchy:
            raise OrganizationError(f"Node '{name}' not found")

        return {
            "parents": list(self._hierarchy.predecessors(name)),
            "children": list(self._hierarchy.successors(name)),
            "metadata": self._hierarchy.nodes[name].get("metadata", {}),
            "type": self._hierarchy.nodes[name]["type"]
        }

    async def suggest_tags(self, content: str, limit: int = 5) -> List[str]:
        """Suggest tags based on content."""
        # Implementation for tag suggestions
        pass

    async def reorganize_notes(self) -> None:
        """Reorganize notes according to hierarchy."""
        # Implementation for note reorganization
        pass 