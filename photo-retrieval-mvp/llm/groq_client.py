"""
llm/groq_client.py
Helper for interacting with the Groq API for text generation.
Supports structured JSON output and retries.
"""

import json
import logging
import os
from typing import Any, Optional

from groq import AsyncGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

logger = logging.getLogger(__name__)

# Default fallback if env var is missing
DEFAULT_MODEL = "openai/gpt-oss-120b"


class GroqClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "dummy_key")
        self.client = AsyncGroq(api_key=self.api_key)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=10),
        reraise=True,
    )
    async def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """
        Generate a JSON response from Groq.
        Forces JSON mode and parses the result.
        """
        resolved_model = model or os.getenv("GROQ_PRIMARY_MODEL", DEFAULT_MODEL)
        response = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            model=resolved_model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq")
            
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Groq JSON: %s\nContent: %s", e, content)
            raise ValueError(f"Invalid JSON from Groq: {e}")

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=10),
        reraise=True,
    )
    async def generate_text(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate plain text response from Groq.
        """
        resolved_model = model or os.getenv("GROQ_PRIMARY_MODEL", DEFAULT_MODEL)
        response = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            model=resolved_model,
            temperature=temperature,
        )
        
        content = response.choices[0].message.content
        if not content:
            return ""
        return content.strip()
