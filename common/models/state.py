from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class WorkerStatus(Enum):
    ACTIVE = "active"
    BUSY = "busy"
    DRAINING = "draining"
    OFFLINE = "offline"

class HealthIssue(BaseModel):
    component: str
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SystemMetrics(BaseModel):
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    load_average: float = 0.0
    network_connections: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentMetrics(BaseModel):
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    memory_usage: float = 0.0
    last_error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentState(BaseModel):
    """State model for agents"""
    id: str
    worker_id: str
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    capabilities: List[str]
    current_task: Optional[str] = None
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)
    error_count: int = 0
    max_errors: int = 3

    class Config:
        use_enum_values = True

class WorkerState(BaseModel):
    """State model for workers"""
    id: str
    status: WorkerStatus = Field(default=WorkerStatus.ACTIVE)
    capabilities: List[str]
    current_tasks: List[str] = Field(default_factory=list)
    current_load: float = 0.0
    max_load: float = 100.0
    agents: List[str] = Field(default_factory=list)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    metrics: SystemMetrics = Field(default_factory=SystemMetrics)

    class Config:
        use_enum_values = True

class HealthStatus(BaseModel):
    """Health status model for system components"""
    status: ComponentStatus
    issues: List[HealthIssue] = Field(default_factory=list)
    metrics: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def needs_attention(self) -> bool:
        return self.status != ComponentStatus.HEALTHY

    @property
    def has_critical_issues(self) -> bool:
        return any(issue.severity == "critical" for issue in self.issues)

    class Config:
        use_enum_values = True