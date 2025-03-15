"""Metrics collection service."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import os
import re
from datetime import datetime
from collections import defaultdict

from ..base_service import BaseService
from ...core.exceptions import AnalysisError


class MetricsCollector(BaseService):
    """Service for collecting vault metrics."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the metrics collector.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self._metrics = defaultdict(dict)
    
    def _initialize(self) -> None:
        """Initialize service-specific resources."""
        pass
    
    async def start(self) -> None:
        """Start the metrics collector service."""
        pass
    
    async def stop(self) -> None:
        """Stop the metrics collector service and cleanup resources."""
        await self.cleanup()
    
    async def health_check(self) -> bool:
        """Check if the service is healthy.
        
        Returns:
            True if service is healthy
        """
        return True
    
    async def collect_vault_metrics(
        self,
        vault_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect metrics from vault.
        
        Args:
            vault_path: Path to vault
            include_patterns: Optional patterns to include
            exclude_patterns: Optional patterns to exclude
            
        Returns:
            Dictionary containing vault metrics
            
        Raises:
            AnalysisError: If metrics collection fails
        """
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "vault_path": str(vault_path),
                "file_metrics": await self._collect_file_metrics(vault_path, include_patterns, exclude_patterns),
                "content_metrics": await self._collect_content_metrics(vault_path, include_patterns, exclude_patterns),
                "link_metrics": await self._collect_link_metrics(vault_path, include_patterns, exclude_patterns),
                "tag_metrics": await self._collect_tag_metrics(vault_path, include_patterns, exclude_patterns)
            }
            
            self._metrics[str(vault_path)][metrics["timestamp"]] = metrics
            return metrics
        except Exception as e:
            raise AnalysisError(f"Failed to collect vault metrics: {str(e)}")
    
    async def _collect_file_metrics(
        self,
        vault_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect file-related metrics.
        
        Args:
            vault_path: Path to vault
            include_patterns: Optional patterns to include
            exclude_patterns: Optional patterns to exclude
            
        Returns:
            Dictionary containing file metrics
        """
        metrics = {
            "total_files": 0,
            "total_folders": 0,
            "file_types": defaultdict(int),
            "folder_sizes": defaultdict(int),
            "folder_depths": defaultdict(int),
            "file_sizes": {
                "min": float("inf"),
                "max": 0,
                "avg": 0,
                "total": 0
            }
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
            
            metrics["total_folders"] += len(dirs)
            depth = len(rel_root.parts)
            metrics["folder_depths"][depth] += 1
            
            for file in files:
                file_path = rel_root / file
                if (not exclude_patterns or not any(
                    re.match(p, str(file_path)) for p in exclude_patterns
                )) and (not include_patterns or any(
                    re.match(p, str(file_path)) for p in include_patterns
                )):
                    metrics["total_files"] += 1
                    ext = Path(file).suffix
                    metrics["file_types"][ext] += 1
                    
                    size = os.path.getsize(vault_path / file_path)
                    metrics["file_sizes"]["min"] = min(metrics["file_sizes"]["min"], size)
                    metrics["file_sizes"]["max"] = max(metrics["file_sizes"]["max"], size)
                    metrics["file_sizes"]["total"] += size
                    metrics["folder_sizes"][str(rel_root)] += size
        
        if metrics["total_files"] > 0:
            metrics["file_sizes"]["avg"] = metrics["file_sizes"]["total"] / metrics["total_files"]
        if metrics["file_sizes"]["min"] == float("inf"):
            metrics["file_sizes"]["min"] = 0
            
        return metrics
    
    async def _collect_content_metrics(
        self,
        vault_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect content-related metrics.
        
        Args:
            vault_path: Path to vault
            include_patterns: Optional patterns to include
            exclude_patterns: Optional patterns to exclude
            
        Returns:
            Dictionary containing content metrics
        """
        metrics = {
            "total_words": 0,
            "total_lines": 0,
            "avg_words_per_file": 0,
            "avg_lines_per_file": 0,
            "files_with_frontmatter": 0,
            "files_with_metadata": 0
        }
        
        file_count = 0
        for root, _, files in os.walk(vault_path):
            rel_root = Path(root).relative_to(vault_path)
            
            for file in files:
                if not file.endswith(".md"):
                    continue
                    
                file_path = rel_root / file
                if (not exclude_patterns or not any(
                    re.match(p, str(file_path)) for p in exclude_patterns
                )) and (not include_patterns or any(
                    re.match(p, str(file_path)) for p in include_patterns
                )):
                    file_count += 1
                    with open(vault_path / file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    lines = content.split("\n")
                    metrics["total_lines"] += len(lines)
                    metrics["total_words"] += len(content.split())
                    
                    if content.startswith("---"):
                        metrics["files_with_frontmatter"] += 1
                    if ":" in content:
                        metrics["files_with_metadata"] += 1
        
        if file_count > 0:
            metrics["avg_words_per_file"] = metrics["total_words"] / file_count
            metrics["avg_lines_per_file"] = metrics["total_lines"] / file_count
            
        return metrics
    
    async def _collect_link_metrics(
        self,
        vault_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect link-related metrics.
        
        Args:
            vault_path: Path to vault
            include_patterns: Optional patterns to include
            exclude_patterns: Optional patterns to exclude
            
        Returns:
            Dictionary containing link metrics
        """
        metrics = {
            "total_links": 0,
            "internal_links": 0,
            "external_links": 0,
            "broken_links": 0,
            "files_with_links": 0,
            "avg_links_per_file": 0
        }
        
        internal_link_pattern = r"\[\[(.*?)\]\]"
        external_link_pattern = r"\[.*?\]\((https?://.*?)\)"
        file_count = 0
        
        for root, _, files in os.walk(vault_path):
            rel_root = Path(root).relative_to(vault_path)
            
            for file in files:
                if not file.endswith(".md"):
                    continue
                    
                file_path = rel_root / file
                if (not exclude_patterns or not any(
                    re.match(p, str(file_path)) for p in exclude_patterns
                )) and (not include_patterns or any(
                    re.match(p, str(file_path)) for p in include_patterns
                )):
                    file_count += 1
                    with open(vault_path / file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    internal_links = re.findall(internal_link_pattern, content)
                    external_links = re.findall(external_link_pattern, content)
                    
                    metrics["internal_links"] += len(internal_links)
                    metrics["external_links"] += len(external_links)
                    metrics["total_links"] += len(internal_links) + len(external_links)
                    
                    if internal_links or external_links:
                        metrics["files_with_links"] += 1
                        
                    # Check for broken internal links
                    for link in internal_links:
                        link_path = vault_path / f"{link}.md"
                        if not link_path.exists():
                            metrics["broken_links"] += 1
        
        if file_count > 0:
            metrics["avg_links_per_file"] = metrics["total_links"] / file_count
            
        return metrics
    
    async def _collect_tag_metrics(
        self,
        vault_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect tag-related metrics.
        
        Args:
            vault_path: Path to vault
            include_patterns: Optional patterns to include
            exclude_patterns: Optional patterns to exclude
            
        Returns:
            Dictionary containing tag metrics
        """
        metrics = {
            "total_tags": 0,
            "unique_tags": set(),
            "files_with_tags": 0,
            "avg_tags_per_file": 0,
            "tag_frequency": defaultdict(int)
        }
        
        tag_pattern = r"#[^\s#]+"
        file_count = 0
        
        for root, _, files in os.walk(vault_path):
            rel_root = Path(root).relative_to(vault_path)
            
            for file in files:
                if not file.endswith(".md"):
                    continue
                    
                file_path = rel_root / file
                if (not exclude_patterns or not any(
                    re.match(p, str(file_path)) for p in exclude_patterns
                )) and (not include_patterns or any(
                    re.match(p, str(file_path)) for p in include_patterns
                )):
                    file_count += 1
                    with open(vault_path / file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    tags = re.findall(tag_pattern, content)
                    if tags:
                        metrics["files_with_tags"] += 1
                        
                    for tag in tags:
                        metrics["total_tags"] += 1
                        metrics["unique_tags"].add(tag)
                        metrics["tag_frequency"][tag] += 1
        
        if file_count > 0:
            metrics["avg_tags_per_file"] = metrics["total_tags"] / file_count
            
        metrics["unique_tags"] = list(metrics["unique_tags"])
        metrics["tag_frequency"] = dict(metrics["tag_frequency"])
            
        return metrics
    
    async def get_metrics_history(
        self,
        vault_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get historical metrics for a vault.
        
        Args:
            vault_path: Path to vault
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of historical metrics
        """
        metrics = self._metrics.get(vault_path, {})
        history = []
        
        for timestamp, data in metrics.items():
            dt = datetime.fromisoformat(timestamp)
            if (not start_time or dt >= start_time) and (not end_time or dt <= end_time):
                history.append(data)
                
        return sorted(history, key=lambda x: x["timestamp"])
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._metrics.clear() 