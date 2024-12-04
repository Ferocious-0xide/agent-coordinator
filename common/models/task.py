from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2

class TaskResult(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

class Task(BaseModel):
    """Base task model for all system tasks"""
    id: str
    type: str
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    payload: Dict
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Optional[TaskResult] = None
    agent_requirements: List[str]
    worker_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    class Config:
        use_enum_values = True

class TaskPackage(BaseModel):
    """Wrapper for tasks with metadata"""
    task: Task
    metadata: Dict = Field(default_factory=dict)
    task_creator: Optional[str] = None
    task_executor: Optional[str] = None
    parent_task: Optional[str] = None
    subtasks: List[str] = Field(default_factory=list)
    completion: str = Field(default="active")
    answer: Optional[str] = None

    def is_complete(self) -> bool:
        return self.completion == "completed"

    def mark_complete(self, answer: str = None):
        self.completion = "completed"
        if answer:
            self.answer = answer