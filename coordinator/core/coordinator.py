from typing import Dict, Optional, List
import asyncio
import logging
from datetime import datetime, timedelta

from coordinator.core.queue import TaskQueue
from coordinator.core.state import StateManager
from coordinator.core.health import HealthMonitor
from common.models.task import Task, TaskStatus, TaskPriority
from common.utils.decorators import log_execution_time, handle_exceptions

logger = logging.getLogger(__name__)

class Coordinator:
    """Main coordinator service managing task distribution and agent orchestration"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.task_queue = TaskQueue(config)
        self.state_manager = StateManager(config)
        self.health_monitor = HealthMonitor(config)
        self.running = False
        self._background_tasks = set()

    async def start(self):
        """Start the coordinator service and background tasks"""
        logger.info("Starting coordinator service")
        self.running = True
        
        # Start background tasks
        self._background_tasks.add(
            asyncio.create_task(self._task_distribution_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._health_check_loop())
        )
        
        logger.info("Coordinator service started")

    async def stop(self):
        """Gracefully stop the coordinator service"""
        logger.info("Stopping coordinator service")
        self.running = False
        
        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()
            
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
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

    async def _task_distribution_loop(self):
        """Background loop for distributing tasks to workers"""
        while self.running:
            try:
                # Get available workers
                available_workers = await self.state_manager.get_available_workers()
                if not available_workers:
                    await asyncio.sleep(1)
                    continue

                # Get next task
                task = await self.task_queue.dequeue()
                if not task:
                    await asyncio.sleep(1)
                    continue

                # Find best worker for task
                worker = await self._select_worker(task, available_workers)
                if worker:
                    await self._assign_task(task, worker)
                else:
                    # Re-queue task if no suitable worker
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

    async def _validate_task(self, task: Task) -> bool:
        """Validate task requirements and constraints"""
        # Check if required agent types are available
        available_agents = await self.state_manager.get_registered_agents()
        required_capabilities = set(task.agent_requirements)
        available_capabilities = set()
        
        for agent in available_agents:
            available_capabilities.update(agent.capabilities)
            
        return required_capabilities.issubset(available_capabilities)

    async def _select_worker(self, task: Task, workers: List[str]) -> Optional[str]:
        """Select best worker for task based on load and capabilities"""
        best_worker = None
        min_load = float('inf')
        
        for worker_id in workers:
            worker_state = await self.state_manager.get_worker_state(worker_id)
            if not worker_state:
                continue
                
            # Check if worker has required capabilities
            if not all(cap in worker_state.capabilities for cap in task.agent_requirements):
                continue
                
            # Select worker with lowest load
            if worker_state.current_load < min_load:
                min_load = worker_state.current_load
                best_worker = worker_id
                
        return best_worker

    async def _assign_task(self, task: Task, worker_id: str):
        """Assign task to worker and update states"""
        logger.info(f"Assigning task {task.id} to worker {worker_id}")
        
        # Update task status
        task.status = TaskStatus.RUNNING
        await self.state_manager.update_task_state(task)
        
        # Update worker state
        await self.state_manager.assign_task_to_worker(task.id, worker_id)
        
        # Notify worker
        await self.state_manager.notify_worker(worker_id, task)

    async def _handle_health_issues(self, health_status):
        """Handle health monitoring alerts"""
        for issue in health_status.issues:
            if issue.severity == 'critical':
                await self._handle_critical_issue(issue)
            elif issue.severity == 'warning':
                await self._handle_warning_issue(issue)

    async def _handle_critical_issue(self, issue):
        """Handle critical health issues"""
        logger.critical(f"Critical health issue detected: {issue}")
        # Implement critical issue handling (e.g., worker restart, task reallocation)

    async def _handle_warning_issue(self, issue):
        """Handle warning health issues"""
        logger.warning(f"Health warning detected: {issue}")
        # Implement warning handling (e.g., load balancing, scaling)