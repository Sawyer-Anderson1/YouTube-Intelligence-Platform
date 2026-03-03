import httpx
import json
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OPENROUTER API Catalog endpoint
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
# LLM Model
MODEL = "openrouter/aurora-alpha"


class LLMClient:
    """
    A client for interacting with OpenRouter LLM API using direct HTTP requests.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = MODEL):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenRouter API key. If not provided, uses OPENROUTER_API_KEY env var.
            model: The model to use for completions.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in OPENROUTER_API_KEY env var")
        
        self.model = model
        self.base_url = OPENROUTER_BASE
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",  # Required by OpenRouter
            "X-Title": "YouTube Intelligence Platform"
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
        
        Returns:
            The API response as a dictionary
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    def chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of chat completion.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter.
        
        Returns:
            List of available models
        """
        response = httpx.get(
            f"{self.base_url}/models",
            headers=self.headers,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json().get("data", [])
    
# Testing
if __name__ == "__main__":
    
    LLMClient = LLMClient()
    
    print("=== Example 0: List Models ===")
    try:
        models = LLMClient.get_models()
        print(f"Available Models: {[model['id'] for model in models]}\n")
    except Exception as e:
        print(f"Error fetching models: {e}\n")
    
    # Example 1: Simple prompt
    print("=== Example 1: Simple Chat ===")
    try:
        response = LLMClient.chat_completion_sync(
            messages=[{"role": "user", "content": "What is the capital of France?"}]
        )
        result = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"Response: {result}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 2: With system prompt
    print("=== Example 2: With System Prompt ===")
    try:
        response = LLMClient.chat_completion_sync(
            messages=[
                {"role": "system", "content": "You are a physics professor. Explain concepts simply."},
                {"role": "user", "content": "Explain gravity"}
            ]
        )
        result = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"Response: {result}\n")
    except Exception as e:
        print(f"Error: {e}\n")
