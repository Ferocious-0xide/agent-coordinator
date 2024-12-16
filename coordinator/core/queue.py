from typing import Optional, Dict
import logging
import asyncio
from datetime import datetime
from redis.asyncio import Redis
import json

from common.models.task import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)

class TaskQueue:
    """Priority-based task queue with Redis backend"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis = Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            password=config['redis'].get('password'),
            db=config['redis'].get('db', 0),
            decode_responses=True
        )

    async def enqueue(self, task: Task, priority: TaskPriority = TaskPriority.MEDIUM) -> bool:
        """Add task to queue with priority"""
        try:
            queue_key = f"task_queue:{priority.value}"
            task_data = task.model_dump_json()
            
            async with self.redis.pipeline() as pipe:
                await pipe.zadd(queue_key, {task.id: datetime.utcnow().timestamp()})
                await pipe.hset(f"task:{task.id}", mapping={"data": task_data})
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
                result = await self.redis.zpopmin(queue_key)
                if not result:
                    continue
                    
                task_id = result[0][0]
                task_data = await self.redis.hget(f"task:{task_id}", "data")
                
                if task_data:
                    return Task.model_validate_json(task_data)
                    
            except Exception as e:
                logger.error(f"Error dequeuing task: {e}")
                
        return None

    async def cancel(self, task_id: str) -> bool:
        """Cancel task if it exists in queue"""
        try:
            for priority in TaskPriority:
                queue_key = f"task_queue:{priority.value}"
                removed = await self.redis.zrem(queue_key, task_id)
                
                if removed:
                    await self.redis.hset(
                        f"task:{task_id}",
                        mapping={"status": TaskStatus.CANCELLED.value}
                    )
                    logger.info(f"Task {task_id} cancelled")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return False

    async def cleanup(self):
        """Remove expired tasks"""
        try:
            expiry = datetime.utcnow().timestamp() - self.config['task']['max_lifetime']
            
            for priority in TaskPriority:
                queue_key = f"task_queue:{priority.value}"
                expired_tasks = await self.redis.zrangebyscore(queue_key, '-inf', expiry)
                
                if expired_tasks:
                    await self.redis.zremrangebyscore(queue_key, '-inf', expiry)
                    pipe = self.redis.pipeline()
                    
                    for task_id in expired_tasks:
                        pipe.hset(f"task:{task_id}", mapping={"status": TaskStatus.FAILED.value})
                    
                    await pipe.execute()
                    logger.info(f"Removed {len(expired_tasks)} expired tasks from {queue_key}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired tasks: {e}")

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

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()