"""Task management service."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, ConfigDict

from ..base_service import BaseService
from ...core.exceptions import InvalidOperationError


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """Task model."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class TaskManager(BaseService):
    """Service for managing organization tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the task manager.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self._tasks: Dict[UUID, Task] = {}
    
    def _initialize(self) -> None:
        """Initialize service-specific resources."""
        pass
    
    async def start(self) -> None:
        """Start the task manager service."""
        pass
    
    async def stop(self) -> None:
        """Stop the task manager service and cleanup resources."""
        await self.cleanup()
    
    async def health_check(self) -> bool:
        """Check if the service is healthy.
        
        Returns:
            True if service is healthy
        """
        return True
    
    async def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task.
        
        Args:
            title: Task title
            description: Task description
            priority: Task priority
            assigned_to: Optional assignee
            tags: Optional list of tags
            metadata: Optional metadata
            
        Returns:
            Created task
        """
        now = datetime.now()
        task = Task(
            id=uuid4(),
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=now,
            updated_at=now,
            assigned_to=assigned_to,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self._tasks[task.id] = task
        return task
    
    async def get_task(self, task_id: UUID) -> Task:
        """Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task
            
        Raises:
            InvalidOperationError: If task not found
        """
        task = self._tasks.get(task_id)
        if not task:
            raise InvalidOperationError(f"Task not found: {task_id}")
        return task
    
    async def update_task(
        self,
        task_id: UUID,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Update a task.
        
        Args:
            task_id: Task ID
            status: Optional new status
            priority: Optional new priority
            assigned_to: Optional new assignee
            tags: Optional new tags
            metadata: Optional new metadata
            
        Returns:
            Updated task
            
        Raises:
            InvalidOperationError: If task not found
        """
        task = await self.get_task(task_id)
        
        if status:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
        
        if priority:
            task.priority = priority
            
        if assigned_to is not None:  # Allow setting to None
            task.assigned_to = assigned_to
            
        if tags is not None:  # Allow setting to empty list
            task.tags = tags
            
        if metadata is not None:  # Allow setting to empty dict
            task.metadata = metadata
            
        task.updated_at = datetime.now()
        return task
    
    async def delete_task(self, task_id: UUID) -> None:
        """Delete a task.
        
        Args:
            task_id: Task ID
            
        Raises:
            InvalidOperationError: If task not found
        """
        if task_id not in self._tasks:
            raise InvalidOperationError(f"Task not found: {task_id}")
        del self._tasks[task_id]
    
    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Task]:
        """List tasks with optional filters.
        
        Args:
            status: Optional status filter
            priority: Optional priority filter
            assigned_to: Optional assignee filter
            tags: Optional tags filter
            
        Returns:
            List of matching tasks
        """
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
            
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
            
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
            
        if tags:
            tasks = [t for t in tasks if all(tag in t.tags for tag in tags)]
            
        return sorted(tasks, key=lambda t: (t.priority.value, t.created_at))
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._tasks.clear() 