"""
Configuration and Constants for the Forecasting Bot
"""
import os
from dataclasses import dataclass
from typing import Optional

import dotenv

# Load environment variables
dotenv.load_dotenv()


@dataclass
class APIConfig:
    """API configuration settings."""

    metaculus_token: Optional[str] = os.getenv("METACULUS_TOKEN")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url: Optional[str] = os.getenv("OPENROUTER_BASE_URL")
    perplexity_api_key: Optional[str] = os.getenv("PERPLEXITY_API_KEY")
    asknews_client_id: Optional[str] = os.getenv("ASKNEWS_CLIENT_ID")
    asknews_secret: Optional[str] = os.getenv("ASKNEWS_SECRET")
    exa_api_key: Optional[str] = os.getenv("EXA_API_KEY")


@dataclass
class BotConfig:
    """Bot behavior configuration."""

    submit_prediction: bool = False
    use_example_questions: bool = True
    num_runs_per_question: int = 1
    skip_previously_forecasted_questions: bool = False
    concurrent_requests_limit: int = 5
    default_model: str = "anthropic/claude-sonnet-4.5"
    default_temperature: float = 0.3
    research_model: str = "o4-mini-deep-research"
    research_temperature: float = 0.7


@dataclass
class MetaculusConfig:
    """Metaculus-specific configuration."""

    api_base_url: str = "https://www.metaculus.com/api"

    # Tournament IDs
    q4_2024_ai_benchmarking_id: int = 32506
    q1_2025_ai_benchmarking_id: int = 32627
    fall_2025_ai_benchmarking_id: str = "fall-aib-2025"
    current_minibench_id: str = "minibench"
    q4_2024_quarterly_cup_id: int = 3672
    q1_2025_quarterly_cup_id: int = 32630
    current_metaculus_cup_id: str = "metaculus-cup"
    axc_2025_tournament_id: int = 32564
    ai_2027_tournament_id: str = "ai-2027"

    # Default tournament to use
    default_tournament_id: str = "fall-aib-2025"


# Example questions for testing
EXAMPLE_QUESTIONS = [
    # (question_id, post_id)
    # (578, 578),  # Human Extinction - Binary
    # (14333, 14333),  # Age of Oldest Human - Numeric
    (22427, 22427),  # Number of New Leading AI Labs - Multiple Choice
    # (38195, 38880),  # Number of US Labor Strikes Due to AI in 2029 - Discrete
]


# Question type constants
class QuestionType:
    """Question type constants."""
    BINARY = "binary"
    NUMERIC = "numeric"
    DISCRETE = "discrete"
    MULTIPLE_CHOICE = "multiple_choice"


# Global configuration instances
api_config = APIConfig()
bot_config = BotConfig()
metaculus_config = MetaculusConfig()
