import os
import re
from pathlib import Path
from typing import List, Optional, Set, Dict

class ObsidianUtils:
    """Utility class for working with Obsidian vaults."""
    
    MARKDOWN_EXTENSIONS = {'.md', '.markdown'}
    WIKILINK_PATTERN = r'\[\[(.*?)\]\]'
    TAG_PATTERN = r'#[^\s#]+'
    
    @staticmethod
    def is_markdown_file(file_path: str) -> bool:
        """Check if a file is a markdown file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file has markdown extension
        """
        return Path(file_path).suffix.lower() in ObsidianUtils.MARKDOWN_EXTENSIONS
    
    @staticmethod
    def extract_wikilinks(content: str) -> Set[str]:
        """Extract wikilinks from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Set of wikilink targets
        """
        matches = re.findall(ObsidianUtils.WIKILINK_PATTERN, content)
        return {match.split('|')[0] for match in matches}
    
    @staticmethod
    def extract_tags(content: str) -> Set[str]:
        """Extract tags from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Set of tags (without #)
        """
        matches = re.findall(ObsidianUtils.TAG_PATTERN, content)
        return {match[1:] for match in matches}  # Remove # prefix
    
    @staticmethod
    def get_vault_files(vault_path: str, 
                       include_patterns: Optional[List[str]] = None,
                       exclude_patterns: Optional[List[str]] = None) -> List[str]:
        """Get all markdown files in vault matching patterns.
        
        Args:
            vault_path: Path to vault root
            include_patterns: Glob patterns to include
            exclude_patterns: Glob patterns to exclude
            
        Returns:
            List of matching file paths
        """
        vault_path = Path(vault_path)
        files = []
        
        for root, _, filenames in os.walk(vault_path):
            for filename in filenames:
                if not ObsidianUtils.is_markdown_file(filename):
                    continue
                    
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(vault_path)
                
                # Check exclude patterns
                if exclude_patterns:
                    excluded = any(relative_path.match(pattern) for pattern in exclude_patterns)
                    if excluded:
                        continue
                        
                # Check include patterns
                if include_patterns:
                    included = any(relative_path.match(pattern) for pattern in include_patterns)
                    if not included:
                        continue
                        
                files.append(str(file_path))
                
        return files
    
    @staticmethod
    def analyze_vault_structure(vault_path: str) -> Dict:
        """Analyze vault structure and return statistics.
        
        Args:
            vault_path: Path to vault root
            
        Returns:
            Dict containing vault statistics
        """
        stats = {
            'total_files': 0,
            'total_links': 0,
            'total_tags': 0,
            'unique_tags': set(),
            'broken_links': set(),
            'orphaned_files': set(),
            'files_by_depth': {}
        }
        
        vault_path = Path(vault_path)
        all_files = set()
        link_graph = {}
        
        # First pass - collect files and extract links
        for file_path in ObsidianUtils.get_vault_files(vault_path):
            relative_path = Path(file_path).relative_to(vault_path)
            all_files.add(str(relative_path))
            
            depth = len(relative_path.parts) - 1
            stats['files_by_depth'][depth] = stats['files_by_depth'].get(depth, 0) + 1
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            links = ObsidianUtils.extract_wikilinks(content)
            tags = ObsidianUtils.extract_tags(content)
            
            stats['total_files'] += 1
            stats['total_links'] += len(links)
            stats['total_tags'] += len(tags)
            stats['unique_tags'].update(tags)
            
            link_graph[str(relative_path)] = links
            
        # Second pass - analyze links
        for source, targets in link_graph.items():
            for target in targets:
                if target not in all_files:
                    stats['broken_links'].add(target)
                    
        # Find orphaned files
        referenced_files = set()
        for targets in link_graph.values():
            referenced_files.update(targets)
            
        stats['orphaned_files'] = all_files - referenced_files
        stats['unique_tags'] = list(stats['unique_tags'])
        stats['broken_links'] = list(stats['broken_links'])
        stats['orphaned_files'] = list(stats['orphaned_files'])
        
        return stats 