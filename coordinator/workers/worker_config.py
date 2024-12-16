from typing import Dict
from pydantic import BaseModel

class WorkerAIConfig(BaseModel):
    """Configuration for worker AI capabilities"""
    
    enabled: bool = True
    default_model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    
    # Rate limiting
    requests_per_minute: int = 60
    concurrent_requests: int = 10
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # Costs and quotas
    cost_per_token: float = 0.00002
    daily_budget: float = 10.0  # USD
    
    @classmethod
    def from_env(cls, env_prefix: str = "HEROKU_AI_") -> "WorkerAIConfig":
        """Create config from environment variables"""
        import os
        
        return cls(
            enabled=os.getenv(f"{env_prefix}ENABLED", "true").lower() == "true",
            default_model=os.getenv(f"{env_prefix}DEFAULT_MODEL", "gpt-4"),
            max_tokens=int(os.getenv(f"{env_prefix}MAX_TOKENS", "1000")),
            temperature=float(os.getenv(f"{env_prefix}TEMPERATURE", "0.7")),
            timeout=int(os.getenv(f"{env_prefix}TIMEOUT", "30")),
            max_retries=int(os.getenv(f"{env_prefix}MAX_RETRIES", "3")),
            requests_per_minute=int(os.getenv(f"{env_prefix}REQUESTS_PER_MINUTE", "60")),
            concurrent_requests=int(os.getenv(f"{env_prefix}CONCURRENT_REQUESTS", "10")),
            cache_enabled=os.getenv(f"{env_prefix}CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv(f"{env_prefix}CACHE_TTL", "3600")),
            cost_per_token=float(os.getenv(f"{env_prefix}COST_PER_TOKEN", "0.00002")),
            daily_budget=float(os.getenv(f"{env_prefix}DAILY_BUDGET", "10.0"))
        )