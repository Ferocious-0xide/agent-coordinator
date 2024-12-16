import logging
from typing import Dict, Optional
from common.integrations.heroku_ai import HerokuAIClient, HerokuAIConfig

logger = logging.getLogger(__name__)

class HerokuAIMixin:
    """Mixin to add Heroku AI capabilities to agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_config = HerokuAIConfig()
        self.ai_client = None
        
    async def setup_ai(self):
        """Initialize AI client"""
        self.ai_client = HerokuAIClient(self.ai_config)
        await self.ai_client.__aenter__()
        
    async def cleanup_ai(self):
        """Cleanup AI client"""
        if self.ai_client:
            await self.ai_client.__aexit__(None, None, None)
            
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Heroku AI"""
        try:
            response = await self.ai_client.generate_completion(prompt, **kwargs)
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
            
    async def get_embeddings(self, texts: list) -> list:
        """Get embeddings using Heroku AI"""
        try:
            response = await self.ai_client.embed_text(texts)
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None