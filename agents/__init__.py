"""
Agent implementations and base classes
"""

from typing import Type, Dict
from agents.base.base_agent import BaseAgent
from agents.base.manager_agent import ManagerAgent
from agents.implementations.search_agent import SearchAgent
from agents.implementations.math_agent import MathAgent
from agents.implementations.plot_agent import PlotAgent

# Agent registry
AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
    'search': SearchAgent,
    'math': MathAgent,
    'plot': PlotAgent,
    'manager': ManagerAgent
}

def get_agent(agent_type: str) -> Type[BaseAgent]:
    """Get agent class by type"""
    if agent_type not in AGENT_TYPES:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return AGENT_TYPES[agent_type]

__all__ = [
    'BaseAgent',
    'ManagerAgent',
    'SearchAgent',
    'MathAgent',
    'PlotAgent',
    'get_agent',
    'AGENT_TYPES'
]