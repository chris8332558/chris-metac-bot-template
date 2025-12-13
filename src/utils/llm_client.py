"""
LLM Client

Wrapper for calling LLM APIs with rate limiting and error handling.
"""
import asyncio
import logging
from typing import Optional

from openai import AsyncOpenAI

from ..config import api_config, bot_config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for making LLM API calls with rate limiting."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        concurrent_limit: int = None,
    ):
        """
        Initialize the LLM client.

        Args:
            base_url: Base URL for the API. If None, uses config.
            api_key: API key. If None, uses config.
            concurrent_limit: Max concurrent requests. If None, uses config.
        """
        self.base_url = base_url or api_config.openrouter_base_url
        self.api_key = api_key or api_config.openrouter_api_key
        self.concurrent_limit = (
            concurrent_limit or bot_config.concurrent_requests_limit
        )
        self.rate_limiter = asyncio.Semaphore(self.concurrent_limit)

        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            max_retries=5,
        )

    async def call(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Make a streaming completion request to the LLM API.

        Args:
            prompt: The prompt to send
            model: Model to use. If None, uses default from config.
            temperature: Temperature setting. If None, uses default from config.

        Returns:
            The LLM's response text

        Raises:
            ValueError: If no response is returned
        """
        if model is None:
            model = bot_config.default_model

        if temperature is None:
            temperature = bot_config.default_temperature

        logger.debug(f"Calling LLM with model={model}, temperature={temperature}")

        # Some models don't support temperature parameter
        models_without_temperature = ["o4-mini-deep-research", "anthropic/claude-sonnet-4.5"]

        async with self.rate_limiter:
            if model in models_without_temperature:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    stream=False,
                )

            answer = response.choices[0].message.content

            if answer is None:
                logger.error("No answer returned from LLM")
                raise ValueError("No answer returned from LLM")

            logger.debug(f"LLM response received (length: {len(answer)} chars)")
            return answer
