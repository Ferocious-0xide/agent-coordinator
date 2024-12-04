from typing import Optional, Dict, List
import asyncio
import logging
from datetime import datetime
import aioredis

from common.models.task import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)

class TaskQueue:
    """Priority-based task queue with Redis backend"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis = None
        self._connect_redis()
        
    async def _connect_redis(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(
            f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
            password=self.config['redis']['password'],
            db=self.config['redis']['db']
        )

    async def enqueue(self, task: Task, priority: TaskPriority = TaskPriority.MEDIUM) -> bool:
        """Add task to queue with priority"""
        try:
            # Create queue key based on priority
            queue_key = f"task_queue:{priority.value}"
            
            # Add task to queue and task details to hash
            async with self.redis.pipeline() as pipe:
                await pipe.zadd(queue_key, {task.id: datetime.utcnow().timestamp()})
                await pipe.hset(f"task:{task.id}", mapping=task.dict())
                await pipe.execute()
                
            logger.debug(f"Task {task.id} enqueued with priority {priority}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueueing task: {e}")
            return False

    async def dequeue(self) -> Optional[Task]:
        """Get highest priority task from queue"""
        for priority in TaskPriority:
            queue_key = f"task_queue:{priority.value}"
            
            try:
                # Get oldest task from highest priority queue
                task_id = await self.redis.zpopmin(queue_key)
                if not task_id:
                    continue
                    
                # Get task details
                task_data = await self.redis.hgetall(f"task:{task_id[0][0]}")
                if task_data:
                    return Task(**task_data)
                    
            except Exception as e:
                logger.error(f"Error dequeuing task: {e}")
                
        return None

    async def cancel(self, task_id: str) -> bool:
        """Cancel task if it exists in queue"""
        try:
            # Check all priority queues
            for priority in TaskPriority:
                queue_key = f"task_queue:{priority.value}"
                
                # Remove from queue if found
                removed = await self.redis.zrem(queue_key, task_id)
                if removed:
                    # Update task status
                    await self.redis.hset(
                        f"task:{task_id}",
                        "status",
                        TaskStatus.CANCELLED.value
                    )
                    logger.info(f"Task {task_id} cancelled")
                    return True
                    
            logger.info(f"Task {task_id} not found in queue")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return False

    async def get_length(self) -> Dict[TaskPriority, int]:
        """Get number of tasks in each priority queue"""
        queue_lengths = {}
        
        try:
            for priority in TaskPriority:
                queue_key = f"task_queue:{priority.value}"
                length = await self.redis.zcard(queue_key)
                queue_lengths[priority] = length
                
        except Exception as e:
            logger.error(f"Error getting queue lengths: {e}")
            
        return queue_lengths

    async def cleanup(self):
        """Remove expired tasks from queues"""
        try:
            expiry = datetime.utcnow().timestamp() - self.config['task']['max_lifetime']
            
            for priority in TaskPriority:
                queue_key = f"task_queue:{priority.value}"
                expired_tasks = await self.redis.zrangebyscore(
                    queue_key, 
                    '-inf', 
                    expiry
                )
                
                if expired_tasks:
                    await self.redis.zremrangebyscore(queue_key, '-inf', expiry)
                    
                    # Update task statuses
                    for task_id in expired_tasks:
                        await self.redis.hset(
                            f"task:{task_id}",
                            "status",
                            TaskStatus.FAILED.value
                        )
                    
                    logger.info(f"Removed {len(expired_tasks)} expired tasks from {queue_key}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired tasks: {e}")