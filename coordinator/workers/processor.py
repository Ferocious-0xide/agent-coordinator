import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime

from common.models.task import Task, TaskStatus, TaskResult, TaskPackage
from common.utils.decorators import log_execution_time, handle_exceptions

logger = logging.getLogger(__name__)

class TaskProcessor:
    """Handles task execution and manages task lifecycle"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_retries = config["worker"]["retry_attempts"]
        self.retry_delay = config["worker"]["retry_delay"]
        
    @log_execution_time
    @handle_exceptions
    async def process_task(self, task: Task, agent: object) -> TaskResult:
        """Process task using specified agent"""
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Create task package
                task_package = self._create_task_package(task)
                
                # Execute task
                result = await self._execute_task(task_package, agent)
                
                if result.success:
                    return result
                    
                # Handle retry
                retry_count += 1
                last_error = result.error
                
                if retry_count <= self.max_retries:
                    await self._handle_retry(task, retry_count)
                    
            except Exception as e:
                logger.error(f"Error processing task {task.id}: {e}")
                retry_count += 1
                last_error = str(e)
                
                if retry_count <= self.max_retries:
                    await self._handle_retry(task, retry_count)
                    
        # Max retries exceeded
        return TaskResult(
            success=False,
            error=f"Max retries exceeded. Last error: {last_error}"
        )
        
    async def _execute_task(self, task_package: TaskPackage, agent: object) -> TaskResult:
        """Execute task using agent"""
        try:
            # Set timeout for task execution
            async with asyncio.timeout(self.config["worker"]["task_timeout"]):
                result = await agent.execute(task_package)
                
            return TaskResult(
                success=True,
                data=result
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_package.task.id} timed out")
            return TaskResult(
                success=False,
                error="Task execution timed out"
            )
        except Exception as e:
            logger.error(f"Error executing task {task_package.task.id}: {e}")
            return TaskResult(
                success=False,
                error=str(e)
            )
            
    def _create_task_package(self, task: Task) -> TaskPackage:
        """Create task package from task"""
        return TaskPackage(
            task=task,
            metadata={
                "processor_id": id(self),
                "attempt": task.retry_count + 1,
                "max_attempts": task.max_retries
            }
        )
        
    async def _handle_retry(self, task: Task, retry_count: int):
        """Handle task retry"""
        task.retry_count = retry_count
        await asyncio.sleep(self.retry_delay * (2 ** (retry_count - 1)))  # Exponential backoff
        
    async def cleanup_task(self, task: Task):
        """Cleanup after task completion"""
        # Implement cleanup logic (e.g., removing temporary files)
        pass