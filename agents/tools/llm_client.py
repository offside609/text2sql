"""
LLM client wrapper for Text-to-SQL agent.

Supports multiple LLM providers (OpenAI, Anthropic, etc.)
"""

from typing import Dict, Any, Optional, List
import os
from pathlib import Path
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables from .env file
# Find .env file relative to project root (sqlagent directory)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> Any:
        """Invoke LLM with prompt and return response."""
        pass
    
    @abstractmethod
    def invoke_structured(self, prompt: str, response_format: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke LLM with structured output."""
        pass


class OpenAILLMClient(LLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model
            self.temperature = temperature
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
        )
        return response.choices[0].message.content
    
    def invoke_structured(self, prompt: str, response_format: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke with structured output (JSON mode)."""
        import json
        
        # Add JSON schema instruction
        json_prompt = f"{prompt}\n\nRespond in valid JSON format matching the schema."
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": json_prompt}],
            temperature=self.temperature,
            response_format={"type": "json_object"} if "json_schema" in response_format else None,
        )
        
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse JSON from LLM response: {content}")


class AnthropicLLMClient(LLMClient):
    """Anthropic Claude LLM client."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.0):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = model
            self.temperature = temperature
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=kwargs.get("temperature", self.temperature),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    
    def invoke_structured(self, prompt: str, response_format: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke with structured output."""
        import json
        
        # Anthropic supports structured output via system prompts
        json_prompt = f"{prompt}\n\nRespond in valid JSON format matching the schema."
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=self.temperature,
            messages=[{"role": "user", "content": json_prompt}],
        )
        
        content = response.content[0].text
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse JSON from LLM response: {content}")


# Global LLM instance
_llm_client: Optional[LLMClient] = None


def get_llm(provider: Optional[str] = None, **kwargs) -> LLMClient:
    """
    Get or create LLM client instance.
    
    Args:
        provider: LLM provider ('openai', 'anthropic'). If None, uses env var LLM_PROVIDER
        **kwargs: Additional arguments for LLM client
        
    Returns:
        LLMClient instance
    """
    global _llm_client
    
    if _llm_client is None:
        provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "openai":
            model = kwargs.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
            _llm_client = OpenAILLMClient(model=model, **kwargs)
        elif provider == "anthropic":
            model = kwargs.get("model", os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"))
            _llm_client = AnthropicLLMClient(model=model, **kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: 'openai', 'anthropic'")
    
    return _llm_client


def reset_llm():
    """Reset global LLM instance (useful for testing)."""
    global _llm_client
    _llm_client = None

