"""
GPT API Client
OpenAI GPT-4 integration
"""

import logging
from typing import List, Dict, Optional, AsyncIterator
import asyncio
from datetime import datetime

import openai
from openai import AsyncOpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class GPTClient:
    """
    GPT API Client
    
    Features:
    - Text generation
    - Chat completion
    - Streaming responses
    - Function calling
    - Token management
    - Error handling & retries
    
    Usage:
        client = GPTClient()
        
        # Generate text
        response = await client.generate(
            prompt="Write an objection letter...",
            max_tokens=1000
        )
        
        # Chat
        response = await client.chat(
            messages=[
                {"role": "system", "content": "You are a legal assistant."},
                {"role": "user", "content": "How do I apply for a personal budget?"}
            ]
        )
    """
    
    # Model configurations
    MODELS = {
        "gpt-4-turbo": {
            "name": "gpt-4-turbo-preview",
            "max_tokens": 128000,
            "cost_per_1k_input": 0.01,
            "cost_per_1k_output": 0.03
        },
        "gpt-4": {
            "name": "gpt-4",
            "max_tokens": 8192,
            "cost_per_1k_input": 0.03,
            "cost_per_1k_output": 0.06
        },
        "gpt-3.5-turbo": {
            "name": "gpt-3.5-turbo",
            "max_tokens": 16385,
            "cost_per_1k_input": 0.0005,
            "cost_per_1k_output": 0.0015
        }
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        stop: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            system_prompt: System instruction
            stop: Stop sequences
        
        Returns:
            Response dict with text and metadata
        """
        
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return await self.chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = None
    ) -> Dict:
        """
        Chat completion
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            stop: Stop sequences
            functions: Available functions
            function_call: Function call mode
        
        Returns:
            Response dict
        """
        
        if temperature is None:
            temperature = self.temperature
        
        model_config = self.MODELS[self.model]
        
        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                functions=functions,
                function_call=function_call
            )
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            # Update usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            
            # Calculate cost
            input_cost = (usage.prompt_tokens / 1000) * model_config["cost_per_1k_input"]
            output_cost = (usage.completion_tokens / 1000) * model_config["cost_per_1k_output"]
            total_cost = input_cost + output_cost
            self.total_cost += total_cost
            
            # Build response
            result = {
                "content": message.content,
                "role": message.role,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "cost": {
                    "input": input_cost,
                    "output": output_cost,
                    "total": total_cost
                },
                "model": model_config["name"]
            }
            
            # Include function call if present
            if message.function_call:
                result["function_call"] = {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments
                }
            
            return result
            
        except Exception as e:
            logger.error(f"GPT API error: {e}", exc_info=True)
            raise
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat completion
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
        
        Yields:
            Text chunks as they arrive
        """
        
        if temperature is None:
            temperature = self.temperature
        
        model_config = self.MODELS[self.model]
        
        try:
            stream = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"GPT streaming error: {e}", exc_info=True)
            raise
    
    async def embed(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """
        Generate text embedding
        
        Args:
            text: Input text
            model: Embedding model
        
        Returns:
            Embedding vector
        """
        
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "model": self.model
        }
    
    def reset_usage_stats(self):
        """Reset usage counters"""
        
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0


# Global GPT client
gpt_client = GPTClient(
    model=settings.gpt_model,
    temperature=settings.gpt_temperature
)