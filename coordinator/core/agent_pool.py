from typing import Dict, List, Optional, Set
import logging
import asyncio
from datetime import datetime

from common.models.state import AgentState
from coordinator.utils.redis_client import RedisClient

logger = logging.getLogger(__name__)

class AgentPool:
    """Manages a pool of available agents and their states"""
    
    def __init__(self, config: Dict, redis_client: RedisClient):
        self.config = config
        self.redis = redis_client
        self.available_agents: Dict[str, AgentState] = {}
        self.busy_agents: Dict[str, AgentState] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}

    async def register_agent(self, agent_id: str, capabilities: List[str], worker_id: str) -> bool:
        """Register a new agent with the pool"""
        try:
            agent_state = AgentState(
                id=agent_id,
                worker_id=worker_id,
                capabilities=capabilities,
                status="idle"
            )
            
            # Store in Redis and local cache
            await self.redis.set_hash(f"agent:{agent_id}", agent_state.dict())
            self.available_agents[agent_id] = agent_state
            self.agent_capabilities[agent_id] = set(capabilities)
            
            logger.info(f"Agent {agent_id} registered with capabilities: {capabilities}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {e}")
            return False

    async def get_agent(self, required_capabilities: List[str]) -> Optional[str]:
        """Get an available agent that matches required capabilities"""
        try:
            for agent_id, capabilities in self.agent_capabilities.items():
                if agent_id in self.available_agents and \
                   all(cap in capabilities for cap in required_capabilities):
                    return agent_id
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent: {e}")
            return None

    async def mark_agent_busy(self, agent_id: str, task_id: str):
        """Mark an agent as busy with a task"""
        if agent_id in self.available_agents:
            agent_state = self.available_agents.pop(agent_id)
            agent_state.status = "busy"
            agent_state.current_task = task_id
            self.busy_agents[agent_id] = agent_state
            await self._update_agent_state(agent_id, agent_state)

    async def mark_agent_available(self, agent_id: str):
        """Mark an agent as available"""
        if agent_id in self.busy_agents:
            agent_state = self.busy_agents.pop(agent_id)
            agent_state.status = "idle"
            agent_state.current_task = None
            self.available_agents[agent_id] = agent_state
            await self._update_agent_state(agent_id, agent_state)

    async def remove_agent(self, agent_id: str):
        """Remove an agent from the pool"""
        self.available_agents.pop(agent_id, None)
        self.busy_agents.pop(agent_id, None)
        self.agent_capabilities.pop(agent_id, None)
        await self.redis.delete(f"agent:{agent_id}")

    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get current state of an agent"""
        if agent_id in self.available_agents:
            return self.available_agents[agent_id]
        if agent_id in self.busy_agents:
            return self.busy_agents[agent_id]
        return None

    async def get_available_agents(self) -> List[str]:
        """Get list of available agent IDs"""
        return list(self.available_agents.keys())

    async def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get list of agent IDs that have a specific capability"""
        return [
            agent_id 
            for agent_id, capabilities in self.agent_capabilities.items() 
            if capability in capabilities
        ]

    async def _update_agent_state(self, agent_id: str, state: AgentState):
        """Update agent state in Redis"""
        await self.redis.set_hash(f"agent:{agent_id}", state.dict())

    async def periodic_cleanup(self):
        """Periodically cleanup stale agent states"""
        while True:
            try:
                # Check for stale agents
                current_time = datetime.utcnow()
                stale_timeout = self.config['monitoring']['health_check_interval'] * 3

                for agents in [self.available_agents, self.busy_agents]:
                    stale_agents = [
                        agent_id 
                        for agent_id, state in agents.items()
                        if (current_time - state.last_heartbeat).total_seconds() > stale_timeout
                    ]
                    
                    for agent_id in stale_agents:
                        logger.warning(f"Removing stale agent {agent_id}")
                        await self.remove_agent(agent_id)

                await asyncio.sleep(self.config['task']['cleanup_interval'])
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying