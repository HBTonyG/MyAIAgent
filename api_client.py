"""
Grok (xAI) API client with rate limiting and error handling.

This module handles:
- API requests with exponential backoff
- Rate limit management
- Error handling and retries
- Response parsing

Note: Grok API is compatible with OpenAI's API structure, so we use the OpenAI SDK
with Grok's base URL.
"""

import time
import openai
from typing import Optional, Dict, Any
import traceback


class APIClient:
    """Grok (xAI) API client with retry logic and rate limiting."""
    
    def __init__(self, api_key: str, model: str = "grok-4-latest", max_retries: int = 5,
                 base_backoff: float = 1.0):
        """
        Initialize API client.
        
        Args:
            api_key: Grok (xAI) API key
            model: Model to use (default: grok-4-latest)
            max_retries: Maximum number of retry attempts
            base_backoff: Base wait time for exponential backoff (seconds)
        """
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        # Grok API is compatible with OpenAI SDK, just change the base URL
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def send_prompt(self, prompt: str, system_prompt: Optional[str] = None,
                   temperature: float = 0.7, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to the Grok API with retry logic.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with 'response', 'model', 'tokens_used', 'error'
            
        Raises:
            Exception: If all retries fail
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else None
                
                return {
                    "response": response_text,
                    "model": self.model,
                    "tokens_used": tokens_used,
                    "error": None
                }
            
            except openai.RateLimitError as e:
                # Rate limit error - use exponential backoff
                wait_time = self.base_backoff * (2 ** attempt)
                if attempt < self.max_retries - 1:
                    print(f"Rate limit hit. Waiting {wait_time:.2f} seconds before retry {attempt + 1}/{self.max_retries}...")
                    time.sleep(wait_time)
                else:
                    return {
                        "response": None,
                        "model": self.model,
                        "tokens_used": None,
                        "error": f"Rate limit error after {self.max_retries} attempts: {str(e)}"
                    }
            
            except openai.APIError as e:
                # Other API errors - retry with backoff
                wait_time = self.base_backoff * (2 ** attempt)
                if attempt < self.max_retries - 1:
                    print(f"API error: {str(e)}. Waiting {wait_time:.2f} seconds before retry {attempt + 1}/{self.max_retries}...")
                    time.sleep(wait_time)
                else:
                    return {
                        "response": None,
                        "model": self.model,
                        "tokens_used": None,
                        "error": f"API error after {self.max_retries} attempts: {str(e)}"
                    }
            
            except Exception as e:
                # Unexpected errors - don't retry, return error
                error_trace = traceback.format_exc()
                return {
                    "response": None,
                    "model": self.model,
                    "tokens_used": None,
                    "error": f"Unexpected error: {str(e)}\n{error_trace}"
                }
        
        # Should not reach here, but just in case
        return {
            "response": None,
            "model": self.model,
            "tokens_used": None,
            "error": "Failed after all retry attempts"
        }
    
    def send_meta_prompt(self, analysis_prompt: str, context: str) -> Dict[str, Any]:
        """
        Send a meta-prompt for self-improvement analysis.
        
        Args:
            analysis_prompt: The meta-prompt asking for analysis
            context: Context data (logs, etc.) to analyze
            
        Returns:
            Dictionary with response and metadata
        """
        full_prompt = f"{analysis_prompt}\n\nContext:\n{context}"
        return self.send_prompt(full_prompt, temperature=0.3)

