from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ContextPattern(BaseModel):
    """Model for context patterns."""
    pattern_id: str
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None

class ContextConfig(BaseModel):
    """Configuration for context management."""
    max_patterns: int = 1000
    min_confidence: float = 0.3
    pattern_storage_path: Path = Path(".context_patterns")
    enable_learning: bool = True

class ContextManager:
    """Enhanced context manager with pattern recognition and learning."""
    
    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()
        self.patterns: Dict[str, ContextPattern] = {}
        self._setup_storage()
        
    def _setup_storage(self):
        """Setup pattern storage."""
        self.config.pattern_storage_path.mkdir(parents=True, exist_ok=True)
        self._load_patterns()
        
    def _load_patterns(self):
        """Load patterns from storage."""
        try:
            for file_path in self.config.pattern_storage_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    pattern_data = json.load(f)
                    pattern = ContextPattern(**pattern_data)
                    self.patterns[pattern.pattern_id] = pattern
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            
    async def analyze_request(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """Analyze user request and build context."""
        context = {}
        
        try:
            # Extract basic context
            context.update(await self._extract_basic_context(user_input))
            
            # Apply context patterns
            context.update(await self._apply_patterns(user_input))
            
            # Add metadata
            context["timestamp"] = datetime.now().isoformat()
            context["request_id"] = f"req_{datetime.now().timestamp()}"
            
            return context
            
        except Exception as e:
            logger.error(f"Request analysis failed: {e}")
            return {"error": str(e)}
            
    async def merge_contexts(
        self,
        *contexts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge multiple contexts with conflict resolution."""
        merged = {}
        conflicts = []
        
        # First pass: collect all keys and detect conflicts
        for context in contexts:
            for key, value in context.items():
                if key in merged:
                    if merged[key] != value:
                        conflicts.append((key, merged[key], value))
                else:
                    merged[key] = value
                    
        # Resolve conflicts
        if conflicts:
            resolved = await self._resolve_conflicts(merged, conflicts)
            merged.update(resolved)
            
        return merged
        
    async def learn_patterns(
        self,
        user_input: str,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """Learn context patterns from interactions."""
        if not self.config.enable_learning:
            return
            
        try:
            # Extract potential patterns
            new_patterns = await self._extract_patterns(
                user_input,
                context,
                result
            )
            
            # Update existing patterns or add new ones
            for pattern in new_patterns:
                if pattern.pattern_id in self.patterns:
                    existing = self.patterns[pattern.pattern_id]
                    # Update confidence based on success
                    if result.get("success", False):
                        existing.confidence = (
                            existing.confidence * 0.9 + 0.1  # Increase confidence
                        )
                    else:
                        existing.confidence *= 0.9  # Decrease confidence
                    
                    existing.usage_count += 1
                    existing.last_used = datetime.now()
                else:
                    # Add new pattern if we have space
                    if len(self.patterns) < self.config.max_patterns:
                        self.patterns[pattern.pattern_id] = pattern
                        
            # Save updated patterns
            await self._save_patterns()
            
        except Exception as e:
            logger.error(f"Pattern learning failed: {e}")
            
    async def optimize_patterns(self):
        """Optimize context patterns."""
        try:
            # Remove low confidence patterns
            self.patterns = {
                pid: pattern
                for pid, pattern in self.patterns.items()
                if pattern.confidence >= self.config.min_confidence
            }
            
            # Save optimized patterns
            await self._save_patterns()
            
        except Exception as e:
            logger.error(f"Pattern optimization failed: {e}")
            
    async def cleanup(self):
        """Clean up context resources."""
        try:
            # Save all patterns
            await self._save_patterns()
            
            # Clear runtime patterns
            self.patterns.clear()
            
        except Exception as e:
            logger.error(f"Context cleanup failed: {e}")
            
    async def _extract_basic_context(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """Extract basic context from user input."""
        context = {
            "input_length": len(user_input),
            "input_type": self._determine_input_type(user_input),
            "tokens": user_input.split(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract entities if present
        entities = await self._extract_entities(user_input)
        if entities:
            context["entities"] = entities
            
        return context
        
    def _determine_input_type(self, user_input: str) -> str:
        """Determine the type of user input."""
        input_lower = user_input.lower()
        
        if "?" in input_lower:
            return "question"
        elif any(cmd in input_lower for cmd in ["create", "add", "make"]):
            return "creation"
        elif any(cmd in input_lower for cmd in ["update", "modify", "change"]):
            return "modification"
        elif any(cmd in input_lower for cmd in ["delete", "remove"]):
            return "deletion"
        elif any(cmd in input_lower for cmd in ["search", "find", "look"]):
            return "search"
        else:
            return "statement"
            
    async def _extract_entities(
        self,
        text: str
    ) -> Optional[Dict[str, List[str]]]:
        """Extract entities from text."""
        # TODO: Implement more sophisticated entity extraction
        entities = {
            "dates": [],
            "numbers": [],
            "paths": [],
            "emails": []
        }
        
        # Simple pattern matching for now
        words = text.split()
        for word in words:
            if word.endswith(".md"):
                entities["paths"].append(word)
            elif "@" in word and "." in word:
                entities["emails"].append(word)
                
        return entities if any(entities.values()) else None
        
    async def _apply_patterns(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """Apply known patterns to extract context."""
        context = {}
        
        for pattern in self.patterns.values():
            if pattern.confidence >= self.config.min_confidence:
                try:
                    if await self._pattern_matches(pattern, user_input):
                        context.update(pattern.pattern_data)
                        pattern.usage_count += 1
                        pattern.last_used = datetime.now()
                except Exception as e:
                    logger.error(f"Pattern application failed: {e}")
                    
        return context
        
    async def _pattern_matches(
        self,
        pattern: ContextPattern,
        user_input: str
    ) -> bool:
        """Check if a pattern matches the user input."""
        try:
            if pattern.pattern_type == "keyword":
                return any(
                    kw.lower() in user_input.lower()
                    for kw in pattern.pattern_data.get("keywords", [])
                )
            elif pattern.pattern_type == "template":
                return self._matches_template(
                    user_input,
                    pattern.pattern_data.get("template", "")
                )
            elif pattern.pattern_type == "regex":
                import re
                return bool(
                    re.search(
                        pattern.pattern_data.get("pattern", ""),
                        user_input
                    )
                )
            return False
        except Exception as e:
            logger.error(f"Pattern matching failed: {e}")
            return False
            
    def _matches_template(
        self,
        text: str,
        template: str
    ) -> bool:
        """Check if text matches a template pattern."""
        # TODO: Implement more sophisticated template matching
        return template.lower() in text.lower()
        
    async def _extract_patterns(
        self,
        user_input: str,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> List[ContextPattern]:
        """Extract new patterns from interaction."""
        patterns = []
        
        try:
            # Extract keyword patterns
            keywords = self._extract_keywords(user_input)
            if keywords:
                patterns.append(ContextPattern(
                    pattern_id=f"kw_{datetime.now().timestamp()}",
                    pattern_type="keyword",
                    pattern_data={"keywords": keywords},
                    confidence=0.5  # Initial confidence
                ))
                
            # Extract template patterns
            template = self._extract_template(user_input, result)
            if template:
                patterns.append(ContextPattern(
                    pattern_id=f"tpl_{datetime.now().timestamp()}",
                    pattern_type="template",
                    pattern_data={"template": template},
                    confidence=0.5
                ))
                
        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            
        return patterns
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        # TODO: Implement more sophisticated keyword extraction
        # For now, just extract words longer than 3 characters
        words = text.lower().split()
        return [w for w in words if len(w) > 3]
        
    def _extract_template(
        self,
        user_input: str,
        result: Dict[str, Any]
    ) -> Optional[str]:
        """Extract a template pattern from successful interaction."""
        if result.get("success", False):
            # TODO: Implement more sophisticated template extraction
            return user_input
        return None
        
    async def _resolve_conflicts(
        self,
        merged: Dict[str, Any],
        conflicts: List[tuple]
    ) -> Dict[str, Any]:
        """Resolve context merge conflicts."""
        resolved = {}
        
        for key, value1, value2 in conflicts:
            # Apply resolution strategies based on key type
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                # For numeric values, take the average
                resolved[key] = (value1 + value2) / 2
            elif isinstance(value1, list) and isinstance(value2, list):
                # For lists, combine unique values
                resolved[key] = list(set(value1 + value2))
            elif isinstance(value1, dict) and isinstance(value2, dict):
                # For dicts, merge recursively
                resolved[key] = {**value1, **value2}
            else:
                # For other types, prefer the more recent value
                resolved[key] = value2
                
        return resolved
        
    async def _save_patterns(self):
        """Save patterns to storage."""
        try:
            for pattern in self.patterns.values():
                file_path = (
                    self.config.pattern_storage_path /
                    f"{pattern.pattern_id}.json"
                )
                with open(file_path, 'w') as f:
                    json.dump(pattern.dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}") 