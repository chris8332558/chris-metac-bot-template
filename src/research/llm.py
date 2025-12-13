"""
LLM Research Provider

Uses an LLM (like o4-mini-deep-research) to conduct research.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from .base import ResearchProvider
from ..config import bot_config
from ..utils import LLMClient
from ..prompts import RESEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMResearchProvider(ResearchProvider):
    """Research provider using LLM for research."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the LLM research provider.

        Args:
            llm_client: LLM client instance. If None, creates a new one.
            model: Model to use for research. If None, uses config default.
            temperature: Temperature for research. If None, uses config default.
        """
        self.llm_client = llm_client or LLMClient()
        self.model = model or bot_config.research_model
        self.temperature = temperature or bot_config.research_temperature

    async def conduct_research(
        self, question: str, question_details: Dict[str, Any] = None
    ) -> str:
        """
        Conduct research using an LLM.

        Args:
            question: The question to research
            question_details: Optional additional details (resolution criteria, fine print, etc.)

        Returns:
            Research findings from the LLM
        """
        logger.info("=" * 20)
        logger.info("Running Research with LLM...")
        logger.info(f"Model: {self.model}")
        logger.info(f"Research Question: '{question}'")
        logger.info("=" * 20)

        # Build a comprehensive query if we have question details
        if question_details:
            query = self._build_detailed_query(question, question_details)
        else:
            query = f"{RESEARCH_SYSTEM_PROMPT}\n\nThe question is: {question}"

        try:
            research = await self.llm_client.call(
                prompt=query,
                model=self.model,
                temperature=self.temperature,
            )

            logger.info("\n======Research Start======")
            logger.info(research)
            logger.info("\n======Research End========")

            return research

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return f"Research could not be completed: {str(e)}"

    def _build_detailed_query(self, question: str, details: Dict[str, Any]) -> str:
        """
        Build a detailed research query including resolution criteria.

        Args:
            question: The base question
            details: Question details dictionary

        Returns:
            Formatted query string
        """
        query_parts = [RESEARCH_SYSTEM_PROMPT]
        query_parts.append(f"\nThe question is: {question}")

        if resolution_criteria := details.get("resolution_criteria"):
            query_parts.append(
                f"\n\nThis question's outcome will be determined by the specific criteria below:"
            )
            query_parts.append(resolution_criteria)

        if fine_print := details.get("fine_print"):
            query_parts.append(f"\n\nFine Print: {fine_print}")

        return "\n".join(query_parts)
