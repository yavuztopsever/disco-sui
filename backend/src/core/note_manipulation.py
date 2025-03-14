from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from .text_processing import TextProcessor
from .exceptions import NoteManipulationError

class NoteMetadata(BaseModel):
    """Metadata for a note."""
    title: str
    tags: List[str] = []
    created: str
    modified: str
    frontmatter: Dict[str, Any] = {}

class NoteManipulator:
    """Unified service for note manipulation operations."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.text_processor = TextProcessor()

    async def merge_notes(
        self,
        source_paths: List[Path],
        target_path: Path,
        merge_strategy: str = "append"
    ) -> Dict[str, Any]:
        """Merge multiple notes into a single note.
        
        Args:
            source_paths: List of paths to source notes
            target_path: Path for the merged note
            merge_strategy: Strategy for merging ("append" or "semantic")
            
        Returns:
            Dictionary containing merge results
        """
        try:
            # Read source notes
            contents = []
            metadata_list = []
            for path in source_paths:
                content = await self._read_note(path)
                metadata = await self._extract_metadata(path, content)
                contents.append(content)
                metadata_list.append(metadata)
            
            # Merge contents based on strategy
            if merge_strategy == "semantic":
                merged_content = await self._semantic_merge(contents, metadata_list)
            else:  # append strategy
                merged_content = self._append_merge(contents, metadata_list)
            
            # Write merged note
            await self._write_note(target_path, merged_content)
            
            # Update links in other notes
            await self._update_links_after_merge(source_paths, target_path)
            
            return {
                "success": True,
                "source_paths": [str(p) for p in source_paths],
                "target_path": str(target_path),
                "strategy": merge_strategy
            }
            
        except Exception as e:
            raise NoteManipulationError(f"Failed to merge notes: {str(e)}")

    async def split_note(
        self,
        source_path: Path,
        split_criteria: str = "heading"
    ) -> Dict[str, Any]:
        """Split a note into multiple notes.
        
        Args:
            source_path: Path to the source note
            split_criteria: Criteria for splitting ("heading" or "semantic")
            
        Returns:
            Dictionary containing split results
        """
        try:
            content = await self._read_note(source_path)
            metadata = await self._extract_metadata(source_path, content)
            
            # Split content based on criteria
            if split_criteria == "semantic":
                split_contents = await self._semantic_split(content)
            else:  # heading-based split
                split_contents = self._heading_split(content)
            
            # Create new notes
            new_paths = []
            for i, split_content in enumerate(split_contents):
                new_path = source_path.parent / f"{source_path.stem}_part{i+1}.md"
                await self._write_note(new_path, split_content)
                new_paths.append(new_path)
            
            # Update links in other notes
            await self._update_links_after_split(source_path, new_paths)
            
            return {
                "success": True,
                "source_path": str(source_path),
                "new_paths": [str(p) for p in new_paths],
                "criteria": split_criteria
            }
            
        except Exception as e:
            raise NoteManipulationError(f"Failed to split note: {str(e)}")

    async def _read_note(self, path: Path) -> str:
        """Read a note's content."""
        try:
            return path.read_text()
        except Exception as e:
            raise NoteManipulationError(f"Failed to read note {path}: {str(e)}")

    async def _write_note(self, path: Path, content: str) -> None:
        """Write content to a note."""
        try:
            path.write_text(content)
        except Exception as e:
            raise NoteManipulationError(f"Failed to write note {path}: {str(e)}")

    async def _extract_metadata(self, path: Path, content: str) -> NoteMetadata:
        """Extract metadata from note content."""
        # Implementation would parse frontmatter and extract metadata
        # Placeholder implementation
        return NoteMetadata(
            title=path.stem,
            created="",
            modified=""
        )

    async def _semantic_merge(
        self,
        contents: List[str],
        metadata_list: List[NoteMetadata]
    ) -> str:
        """Merge notes based on semantic analysis."""
        # This would use LLM to intelligently merge content
        # Placeholder implementation returns simple concatenation
        return "\n\n".join(contents)

    def _append_merge(
        self,
        contents: List[str],
        metadata_list: List[NoteMetadata]
    ) -> str:
        """Merge notes by appending with clear separators."""
        merged = []
        for i, (content, metadata) in enumerate(zip(contents, metadata_list)):
            if i > 0:
                merged.append("\n---\n")  # Section separator
            merged.append(f"# {metadata.title}\n")
            merged.append(content)
        return "\n".join(merged)

    def _heading_split(self, content: str) -> List[str]:
        """Split note based on headings."""
        import re
        # Split on top-level headings
        parts = re.split(r'^#\s', content, flags=re.MULTILINE)
        # Clean and filter parts
        return [p.strip() for p in parts if p.strip()]

    async def _semantic_split(self, content: str) -> List[str]:
        """Split note based on semantic analysis."""
        # This would use LLM to intelligently split content
        # Placeholder implementation uses heading split
        return self._heading_split(content)

    async def _update_links_after_merge(
        self,
        source_paths: List[Path],
        target_path: Path
    ) -> None:
        """Update links in other notes after a merge operation."""
        # Implementation would update all internal links
        pass

    async def _update_links_after_split(
        self,
        source_path: Path,
        new_paths: List[Path]
    ) -> None:
        """Update links in other notes after a split operation."""
        # Implementation would update all internal links
        pass 