import os
import logging
import aiohttp
from typing import Dict, Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class HerokuAIConfig(BaseModel):
    api_key: str = os.getenv('HEROKU_AI_API_KEY')
    base_url: str = os.getenv('HEROKU_AI_URL', 'https://ai-api.heroku.com/v1')
    max_retries: int = 3
    timeout: int = 30

class HerokuAIClient:
    """Client for interacting with Heroku AI add-on"""
    
    def __init__(self, config: Optional[HerokuAIConfig] = None):
        self.config = config or HerokuAIConfig()
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def generate_completion(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict:
        """Generate completion using Heroku AI"""
        endpoint = f"{self.config.base_url}/completions"
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            response.raise_for_status()
            return await response.json()
            
    async def embed_text(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> Dict:
        """Generate embeddings using Heroku AI"""
        endpoint = f"{self.config.base_url}/embeddings"
        payload = {
            "model": model,
            "input": texts
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            response.raise_for_status()
            return await response.json()