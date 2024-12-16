from typing import Dict, Optional
import logging
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from coordinator.core.queue import TaskQueue
from coordinator.core.state import StateManager
from coordinator.core.health import HealthMonitor
from coordinator.core.agent_pool import AgentPool
from coordinator.utils.redis_client import RedisClient
from common.models.task import Task, TaskStatus, TaskPriority
from common.utils.decorators import log_execution_time, handle_exceptions

logger = logging.getLogger(__name__)

class CoordinatorService:
    """Main coordinator service managing task distribution and agent orchestration"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis_client = RedisClient(config)
        self.task_queue = TaskQueue(config)
        self.state_manager = StateManager(config)
        self.health_monitor = HealthMonitor(config)
        self.agent_pool = AgentPool(config, self.redis_client)
        self.running = False
        self._background_tasks = set()

    async def start(self):
        """Start coordinator service and background tasks"""
        logger.info("Starting coordinator service")
        self.running = True
        
        # Start background tasks
        self._background_tasks.add(
            asyncio.create_task(self._task_distribution_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._health_check_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._cleanup_loop())
        )
        
        logger.info("Coordinator service started")

    async def stop(self):
        """Gracefully stop the coordinator service"""
        logger.info("Stopping coordinator service")
        self.running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Clean up resources
        await self.redis_client.close()
        logger.info("Coordinator service stopped")

    @log_execution_time
    @handle_exceptions
    async def submit_task(self, task: Task) -> str:
        """Submit a new task to the system"""
        logger.info(f"Submitting task: {task.id}")
        
        # Validate task requirements
        if not await self._validate_task(task):
            raise ValueError("Task validation failed")
            
        # Enqueue task
        await self.task_queue.enqueue(task, task.priority)
        return task.id

    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Get current status of a task"""
        return await self.state_manager.get_task_status(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or pending task"""
        return await self.task_queue.cancel(task_id)

    async def register_worker(self, worker_id: str, capabilities: list) -> bool:
        """Register a new worker"""
        return await self.state_manager.register_worker(worker_id, capabilities)

    async def deregister_worker(self, worker_id: str) -> bool:
        """Deregister a worker"""
        return await self.state_manager.deregister_worker(worker_id)

    async def _task_distribution_loop(self):
        """Background loop for distributing tasks to workers"""
        while self.running:
            try:
                # Get available agents
                available_agents = await self.agent_pool.get_available_agents()
                if not available_agents:
                    await asyncio.sleep(1)
                    continue

                # Get next task
                task = await self.task_queue.dequeue()
                if not task:
                    await asyncio.sleep(1)
                    continue

                # Find best agent for task
                agent_id = await self._select_agent(task, available_agents)
                if agent_id:
                    await self._assign_task(task, agent_id)
                else:
                    # Re-queue task if no suitable agent
                    await self.task_queue.enqueue(task, task.priority)
                    
            except Exception as e:
                logger.error(f"Error in task distribution loop: {e}")
                await asyncio.sleep(1)

    async def _health_check_loop(self):
        """Background loop for health monitoring"""
        while self.running:
            try:
                health_status = await self.health_monitor.check_system_health()
                if health_status.needs_attention:
                    await self._handle_health_issues(health_status)
                await asyncio.sleep(self.config['monitoring']['health_check_interval'])
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(1)

    async def _cleanup_loop(self):
        """Background loop for cleanup tasks"""
        while self.running:
            try:
                await self.task_queue.cleanup()
                await self.state_manager.cleanup_stale_states()
                await self.agent_pool.periodic_cleanup()
                await asyncio.sleep(self.config['task']['cleanup_interval'])
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(1)

    async def _select_agent(self, task: Task, available_agents: list) -> Optional[str]:
        """Select best agent for task based on capabilities and load"""
        return await self.agent_pool.get_agent(task.agent_requirements)

    async def _assign_task(self, task: Task, agent_id: str):
        """Assign task to agent and update states"""
        logger.info(f"Assigning task {task.id} to agent {agent_id}")
        
        # Update task status
        task.status = TaskStatus.RUNNING
        await self.state_manager.update_task_state(task)
        
        # Update agent state
        await self.agent_pool.mark_agent_busy(agent_id, task.id)

# FastAPI Application
app = FastAPI(title="Agent Coordinator Service")
coordinator: Optional[CoordinatorService] = None

@app.on_event("startup")
async def startup_event():
    """Initialize coordinator on startup"""
    global coordinator
    config = {}  # Load config from environment/files
    coordinator = CoordinatorService(config)
    await coordinator.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global coordinator
    if coordinator:
        await coordinator.stop()

class TaskSubmission(BaseModel):
    type: str
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: Dict
    agent_requirements: list

@app.post("/tasks")
async def submit_task(task_submission: TaskSubmission):
    """Submit a new task"""
    task = Task(
        id=str(uuid.uuid4()),
        type=task_submission.type,
        priority=task_submission.priority,
        payload=task_submission.payload,
        agent_requirements=task_submission.agent_requirements
    )
    task_id = await coordinator.submit_task(task)
    return {"task_id": task_id}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    status = await coordinator.get_task_status(task_id)
    return {"status": status}

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel task"""
    success = await coordinator.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    health_status = await coordinator.health_monitor.check_system_health()
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)