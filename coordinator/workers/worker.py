import asyncio
import logging
import signal
import psutil
import os
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI
import uvicorn

from coordinator.workers.processor import TaskProcessor
from coordinator.utils.redis_client import RedisClient
from coordinator.utils.metrics import MetricsCollector
from common.models.task import Task, TaskStatus, TaskResult
from common.models.state import WorkerState
from common.utils.decorators import log_execution_time, handle_exceptions

logger = logging.getLogger(__name__)

class Worker:
    """Worker process that manages task execution and agent lifecycle"""
    
    def __init__(self, worker_id: str, config: Dict):
        self.id = worker_id
        self.config = config
        self.redis_client = RedisClient(config)
        self.processor = TaskProcessor(config)
        self.metrics = MetricsCollector()
        self.running = False
        self.current_tasks = {}  # task_id -> Task
        self.state = WorkerState(
            id=worker_id,
            status="active",
            current_load=0,
            max_load=config['worker'].get('max_concurrent_tasks', 10)
        )

    async def start(self):
        """Initialize and start the worker"""
        logger.info(f"Starting worker {self.id}")
        self.running = True
        
        # Register with coordinator
        await self._register_with_coordinator()
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._metrics_loop()),
            asyncio.create_task(self._task_monitoring_loop())
        ]
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
            
        logger.info(f"Worker {self.id} started")

    async def stop(self):
        """Gracefully shutdown the worker"""
        logger.info(f"Stopping worker {self.id}")
        self.running = False
        
        # Wait for current tasks to complete
        await self._wait_for_tasks()
        
        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Deregister from coordinator
        await self._deregister_from_coordinator()
        
        # Cleanup connections
        await self.redis_client.close()
        
        logger.info(f"Worker {self.id} stopped")

    @log_execution_time
    async def process_task(self, task: Task) -> TaskResult:
        """Process a task"""
        logger.info(f"Processing task {task.id}")
        
        if len(self.current_tasks) >= self.state.max_load:
            return TaskResult(
                success=False,
                error="Worker at maximum capacity"
            )
            
        try:
            # Update state
            self.current_tasks[task.id] = task
            self.state.current_load = len(self.current_tasks)
            await self._update_state()
            
            # Start metrics tracking
            self.metrics.start_task_timer(task.id, task.type)
            
            # Process task
            result = await self.processor.process_task(task)
            
            # Update metrics
            self.metrics.stop_task_timer(task.id, 
                "completed" if result.success else "failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            return TaskResult(
                success=False,
                error=str(e)
            )
        finally:
            # Cleanup
            self.current_tasks.pop(task.id, None)
            self.state.current_load = len(self.current_tasks)
            await self._update_state()

    async def _register_with_coordinator(self):
        """Register worker with coordinator"""
        capabilities = self.processor.get_capabilities()
        registration_data = {
            "worker_id": self.id,
            "capabilities": capabilities,
            "max_tasks": self.state.max_load,
            "resources": self._get_resource_info()
        }
        
        success = await self.redis_client.publish(
            "worker_registration",
            registration_data
        )
        
        if not success:
            raise RuntimeError("Failed to register with coordinator")

    async def _deregister_from_coordinator(self):
        """Deregister worker from coordinator"""
        await self.redis_client.publish(
            "worker_deregistration",
            {"worker_id": self.id}
        )

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                heartbeat_data = {
                    "worker_id": self.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": self.state.status,
                    "current_load": self.state.current_load,
                    "tasks": list(self.current_tasks.keys())
                }
                
                await self.redis_client.publish(
                    "worker_heartbeat",
                    heartbeat_data
                )
                
                await asyncio.sleep(
                    self.config['monitoring']['heartbeat_interval']
                )
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1)

    async def _metrics_loop(self):
        """Collect and report metrics"""
        while self.running:
            try:
                metrics_data = {
                    "worker_id": self.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "resources": self._get_resource_info(),
                    "tasks_processed": self.metrics.get_metrics_summary(),
                }
                
                await self.redis_client.publish(
                    "worker_metrics",
                    metrics_data
                )
                
                await asyncio.sleep(
                    self.config['monitoring']['metrics_interval']
                )
                
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(1)

    async def _task_monitoring_loop(self):
        """Monitor task execution and handle timeouts"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                timeout = self.config['worker']['task_timeout']
                
                for task_id, task in list(self.current_tasks.items()):
                    if (current_time - task.started_at).total_seconds() > timeout:
                        logger.warning(f"Task {task_id} timed out")
                        await self._handle_task_timeout(task_id)
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in task monitoring loop: {e}")
                await asyncio.sleep(1)

    def _get_resource_info(self) -> Dict:
        """Get current resource usage"""
        process = psutil.Process(os.getpid())
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "num_threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }

    async def _update_state(self):
        """Update worker state in Redis"""
        await self.redis_client.set_hash(
            f"worker:{self.id}",
            self.state.dict()
        )

    async def _wait_for_tasks(self):
        """Wait for current tasks to complete"""
        if self.current_tasks:
            logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete")
            timeout = self.config['worker']['shutdown_timeout']
            try:
                async with asyncio.timeout(timeout):
                    while self.current_tasks:
                        await asyncio.sleep(1)
            except asyncio.TimeoutError:
                logger.warning("Shutdown timeout reached, some tasks may be incomplete")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.stop())

    async def _handle_task_timeout(self, task_id: str):
        """Handle task timeout"""
        task = self.current_tasks.get(task_id)
        if task:
            result = TaskResult(
                success=False,
                error="Task timed out"
            )
            await self.processor.handle_task_completion(task, result)
            self.current_tasks.pop(task_id, None)
            self.state.current_load = len(self.current_tasks)
            await self._update_state()

# FastAPI application for worker API
app = FastAPI(title="Worker Service")
worker: Optional[Worker] = None

@app.on_event("startup")
async def startup_event():
    """Initialize worker on startup"""
    global worker
    config = {}  # Load config from environment/files
    worker_id = f"worker_{os.getpid()}"
    worker = Worker(worker_id, config)
    await worker.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global worker
    if worker:
        await worker.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "worker_id": worker.id if worker else None,
        "current_load": worker.state.current_load if worker else None,
        "resources": worker._get_resource_info() if worker else None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))