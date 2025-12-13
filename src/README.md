# Refactored Forecasting Bot

This is a clean, modular refactoring of the original `main_with_no_framework.py` file.

## Architecture

The codebase follows clean architecture principles with clear separation of concerns:

```
src/
├── config.py              # Configuration and constants
├── api/                   # API clients
│   └── metaculus_client.py
├── research/              # Research providers
│   ├── base.py           # Abstract base class
│   ├── llm.py            # LLM-based research
│   ├── perplexity.py     # Perplexity API
│   └── asknews.py        # AskNews SDK
├── forecasting/           # Forecasting logic by question type
│   ├── binary.py
│   ├── numeric.py
│   └── multiple_choice.py
├── prompts/               # Prompt templates
│   └── templates.py
├── utils/                 # Utilities
│   ├── llm_client.py     # LLM client wrapper
│   └── extractors.py     # Response parsing
└── main.py                # Main entry point
```

## Key Improvements

### 1. **Modular Design**
- Separated concerns into distinct modules
- Each module has a single, well-defined responsibility
- Easy to test and maintain

### 2. **Configuration Management**
- Centralized configuration in `config.py`
- Uses dataclasses for type safety
- Environment variables loaded once

### 3. **Type Safety**
- Type hints throughout the codebase
- Better IDE support and error detection

### 4. **Extensibility**
- Abstract base classes for research providers
- Easy to add new research sources
- Pluggable architecture

### 5. **Error Handling**
- Proper exception handling
- Informative error messages
- Graceful degradation

### 6. **Logging**
- Structured logging throughout
- Different log levels for different severity
- Easy to debug and monitor

### 7. **Code Reusability**
- DRY principle applied
- Shared utilities extracted
- No code duplication

## Usage

### Basic Usage

```python
# Run from the project root
python -m src.main
```

### Configuration

Edit `src/config.py` or set environment variables:

```bash
# Required
export METACULUS_TOKEN="your_token"
export OPENROUTER_API_KEY="your_key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# Optional (for different research providers)
export PERPLEXITY_API_KEY="your_key"
export ASKNEWS_CLIENT_ID="your_id"
export ASKNEWS_SECRET="your_secret"
```

### Programmatic Usage

```python
from src import ForecastingBot
from src.config import bot_config

# Configure
bot_config.submit_prediction = False
bot_config.num_runs_per_question = 3

# Run
bot = ForecastingBot()
await bot.forecast_questions([(question_id, post_id)])
```

## Adding New Features

### Adding a New Research Provider

1. Create a new file in `src/research/`
2. Inherit from `ResearchProvider`
3. Implement `conduct_research()` method
4. Register in `src/research/__init__.py`

Example:
```python
from .base import ResearchProvider

class CustomResearchProvider(ResearchProvider):
    async def conduct_research(self, question, question_details=None):
        # Your implementation
        return research_results
```

### Adding a New Question Type

1. Create a new forecaster in `src/forecasting/`
2. Follow the pattern of existing forecasters
3. Add to the main orchestration in `src/main.py`

## Testing

```bash
# Set test mode
export USE_EXAMPLE_QUESTIONS=True
export SUBMIT_PREDICTION=False

# Run
python -m src.main
```

## Benefits Over Original Code

1. **Maintainability**: Easy to find and modify specific functionality
2. **Testability**: Each module can be tested independently
3. **Readability**: Clear structure and naming conventions
4. **Scalability**: Easy to add new features without modifying existing code
5. **Debugging**: Better logging and error messages
6. **Collaboration**: Multiple developers can work on different modules
