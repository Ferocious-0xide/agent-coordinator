import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from common.models.task import Task, TaskStatus, TaskResult
from common.models.state import WorkerState, AgentState, WorkerStatus
from common.utils.decorators import log_execution_time, handle_exceptions
from coordinator.workers.processor import TaskProcessor
from agents import get_agent

logger = logging.getLogger(__name__)

class Worker:
    """Worker process that manages agents and executes tasks"""
    
    def __init__(self, worker_id: str, config: Dict):
        self.id = worker_id
        self.config = config
        self.processor = TaskProcessor(config)
        self.agents = {}  # agent_id -> agent instance
        self.running = False
        self.state = WorkerState(
            id=worker_id,
            capabilities=[],
            status=WorkerStatus.ACTIVE
        )
        
    async def start(self):
        """Start worker and initialize agents"""
        logger.info(f"Starting worker {self.id}")
        self.running = True
        
        # Initialize configured agents
        await self._initialize_agents()
        
        # Start background tasks
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._metrics_collection_loop())
        
        logger.info(f"Worker {self.id} started with {len(self.agents)} agents")
        
    async def stop(self):
        """Gracefully stop worker"""
        logger.info(f"Stopping worker {self.id}")
        self.running = False
        self.state.status = WorkerStatus.DRAINING
        
        # Wait for current tasks to complete
        while self.state.current_tasks:
            await asyncio.sleep(1)
            
        # Shutdown agents
        for agent in self.agents.values():
            await agent.shutdown()
            
        logger.info(f"Worker {self.id} stopped")
        
    @log_execution_time
    @handle_exceptions
    async def process_task(self, task: Task) -> TaskResult:
        """Process a task using appropriate agent"""
        logger.info(f"Processing task {task.id}")
        
        # Validate task can be processed
        if not self._can_process_task(task):
            return TaskResult(
                success=False,
                error="Worker missing required capabilities"
            )
            
        # Update state
        self.state.current_tasks.append(task.id)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            # Get appropriate agent
            agent = await self._get_agent_for_task(task)
            if not agent:
                raise ValueError("No suitable agent found for task")
                
            # Process task
            result = await self.processor.process_task(task, agent)
            
            # Update task status
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            return TaskResult(
                success=False,
                error=str(e)
            )
        finally:
            # Update state
            self.state.current_tasks.remove(task.id)
            
    async def get_status(self) -> Dict:
        """Get worker status and metrics"""
        return {
            "id": self.id,
            "status": self.state.status,
            "current_load": self.state.current_load,
            "agent_count": len(self.agents),
            "active_tasks": len(self.state.current_tasks),
            "capabilities": self.state.capabilities,
            "metrics": self.state.metrics.dict()
        }
        
    async def _initialize_agents(self):
        """Initialize configured agents"""
        agent_configs = self.config.get("agents", [])
        
        for agent_config in agent_configs:
            try:
                agent_type = agent_config["type"]
                agent_id = f"{self.id}_{agent_type}_{len(self.agents)}"
                
                # Create agent instance
                AgentClass = get_agent(agent_type)
                agent = AgentClass(
                    agent_id=agent_id,
                    worker_id=self.id,
                    config=agent_config
                )
                
                # Initialize agent
                await agent.initialize()
                
                # Store agent
                self.agents[agent_id] = agent
                self.state.agents.append(agent_id)
                self.state.capabilities.extend(agent.get_capabilities())
                
                logger.info(f"Initialized agent {agent_id} of type {agent_type}")
                
            except Exception as e:
                logger.error(f"Error initializing agent: {e}")
                
    async def _get_agent_for_task(self, task: Task) -> Optional[object]:
        """Get appropriate agent for task based on requirements"""
        for agent in self.agents.values():
            if all(cap in agent.get_capabilities() for cap in task.agent_requirements):
                return agent
        return None
        
    def _can_process_task(self, task: Task) -> bool:
        """Check if worker can process task"""
        return (
            self.state.status == WorkerStatus.ACTIVE and
            self.state.current_load < self.state.max_load and
            all(cap in self.state.capabilities for cap in task.agent_requirements)
        )
        
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to coordinator"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config["worker"]["heartbeat_interval"])
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1)
                
    async def _metrics_collection_loop(self):
        """Collect and report metrics periodically"""
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.config["worker"]["metrics_interval"])
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(1)
                
    async def _send_heartbeat(self):
        """Send heartbeat to coordinator"""
        self.state.last_heartbeat = datetime.utcnow()
        await self.state_manager.update_worker_state(self.id, self.state)
        
    async def _collect_metrics(self):
        """Collect metrics from system and agents"""
        # Update system metrics
        self.state.metrics = await self._get_system_metrics()
        
        # Update agent metrics
        for agent in self.agents.values():
            agent_metrics = await agent.get_metrics()
            await self.state_manager.update_agent_metrics(agent.id, agent_metrics)