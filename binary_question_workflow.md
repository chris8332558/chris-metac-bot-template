# Binary Question Prediction Workflow (main_with_no_framework.py)

This document describes the complete step-by-step workflow for predicting a binary question using the bare-metal implementation in `main_with_no_framework.py`.

---

## Phase 1: Initialization (Lines 1097-1110)

```python
# 1. Script starts
if __name__ == "__main__":
    # 2. Get questions to forecast on
    if USE_EXAMPLE_QUESTIONS:
        open_question_id_post_id = EXAMPLE_QUESTIONS  # Line 1099
    else:
        open_question_id_post_id = get_open_question_ids_from_tournament()  # Line 1101

    # 3. Kick off forecasting
    asyncio.run(
        forecast_questions(
            open_question_id_post_id,
            SUBMIT_PREDICTION,
            NUM_RUNS_PER_QUESTION,  # Default: 5 predictions
            SKIP_PREVIOUSLY_FORECASTED_QUESTIONS,
        )
    )
```

---

## Phase 2: Question Orchestration (Lines 1055-1092)

```python
async def forecast_questions(...):
    # 4. Create async tasks for all questions (parallel execution)
    forecast_tasks = [
        forecast_individual_question(question_id, post_id, ...)
        for question_id, post_id in open_question_id_post_id
    ]  # Lines 1061-1069

    # 5. Execute all questions concurrently
    forecast_summaries = await asyncio.gather(*forecast_tasks, return_exceptions=True)  # Line 1071
```

---

## Phase 3: Individual Question Processing (Lines 989-1052)

```python
async def forecast_individual_question(question_id, post_id, ...):
    # 6. Fetch question details from Metaculus API
    post_details = get_post_details(post_id)  # Line 996
    question_details = post_details["question"]
    question_type = question_details["type"]  # Should be "binary"

    # 7. Check if already forecasted (skip if configured)
    if forecast_is_already_made(post_details) and skip_previously_forecasted_questions:
        return "Skipped: Forecast already made"  # Lines 1009-1014

    # 8. Route to binary prediction function
    if question_type == "binary":
        forecast, comment = await get_binary_gpt_prediction(
            question_details,
            num_runs_per_question  # e.g., 5
        )  # Lines 1016-1019
```

---

## Phase 4: Binary Prediction Generation (Lines 438-485)

```python
async def get_binary_gpt_prediction(question_details: dict, num_runs: int):
    # 9. Extract question metadata
    today = datetime.datetime.now().strftime("%Y-%m-%d")  # Line 442
    title = question_details["title"]
    resolution_criteria = question_details["resolution_criteria"]
    background = question_details["description"]
    fine_print = question_details["fine_print"]

    # 10. Run research (CRITICAL STEP)
    summary_report = run_research(title)  # Line 449
    # ↓ Calls one of: AskNews, Exa, or Perplexity (Lines 257-270)

    # 11. Build the forecasting prompt
    content = BINARY_PROMPT_TEMPLATE.format(
        title=title,
        today=today,
        background=background,
        resolution_criteria=resolution_criteria,
        fine_print=fine_print,
        summary_report=summary_report,
    )  # Lines 451-458
```

### The Prompt Template (Lines 392-422)

```
You are a professional forecaster interviewing for a job.

Your interview question is:
{title}

Question background:
{background}

Resolution criteria:
{resolution_criteria}

{fine_print}

Your research assistant says:
{summary_report}

Today is {today}.

Before answering you write:
(a) The time left until the outcome to the question is known.
(b) The status quo outcome if nothing changed.
(c) A brief description of a scenario that results in a No outcome.
(d) A brief description of a scenario that results in a Yes outcome.

You write your rationale remembering that good forecasters put extra weight
on the status quo outcome since the world changes slowly most of the time.

The last thing you write is your final answer as: "Probability: ZZ%", 0-100
```

---

## Phase 5: Parallel LLM Execution (Lines 460-474)

```python
    # 12. Define single prediction function
    async def get_rationale_and_probability(content: str) -> tuple[float, str]:
        # Call LLM with prompt
        rationale = await call_llm(content)  # Line 461
        # ↓ Uses AsyncOpenAI with semaphore rate limiting (Lines 234-254)

        # Extract probability using regex
        probability = extract_probability_from_response_as_percentage_not_decimal(rationale)  # Line 463
        # ↓ Finds last "XX%" in response, clamps to 1-99 (Lines 425-435)

        comment = f"Extracted Probability: {probability}%\n\nGPT's Answer: {rationale}\n\n\n"
        return probability, comment  # Lines 466-470

    # 13. Run N predictions IN PARALLEL (e.g., 5 times)
    probability_and_comment_pairs = await asyncio.gather(
        *[get_rationale_and_probability(content) for _ in range(num_runs)]
    )  # Lines 472-474
```

**Key Detail**: Each of the 5 runs gets the SAME research report but generates independent predictions (temperature=0.3 adds randomness).

---

## Phase 6: Aggregation (Lines 475-485)

```python
    # 14. Extract all probabilities and comments
    comments = [pair[1] for pair in probability_and_comment_pairs]  # Line 475
    probabilities = [pair[0] for pair in probability_and_comment_pairs]  # Line 479

    # 15. Aggregate using MEDIAN (robust to outliers)
    median_probability = float(np.median(probabilities)) / 100  # Line 480
    # Note: Converts from percentage (1-99) to decimal (0.01-0.99)

    # 16. Format final comment
    final_comment = f"Median Probability: {median_probability}\n\n" + "\n\n".join(
        [f"## Rationale {i+1}\n{comment}" for i, comment in enumerate(comments)]
    )  # Lines 482-484

    return median_probability, final_comment  # Line 485
```

---

## Phase 7: Submission to Metaculus (Lines 1046-1050)

```python
    # Back in forecast_individual_question()...

    # 17. Create API payload
    if submit_prediction == True:
        forecast_payload = create_forecast_payload(forecast, question_type)  # Line 1047
        # ↓ For binary: {"probability_yes": forecast, ...} (Lines 130-160)

        # 18. POST prediction to Metaculus
        post_question_prediction(question_id, forecast_payload)  # Line 1048
        # ↓ HTTP POST to /api/questions/forecast/ (Lines 110-127)

        # 19. POST reasoning comment
        post_question_comment(post_id, comment)  # Line 1049
        # ↓ HTTP POST to /api/comments/create/ (Lines 90-107)
```

---

## Complete Flow Diagram

```
START
  │
  ├─> Get question IDs (tournament or examples)
  │
  ├─> FOR EACH QUESTION (in parallel):
  │     │
  │     ├─> Fetch question details from API
  │     │
  │     ├─> Check if already forecasted → SKIP if yes
  │     │
  │     ├─> Detect question type → "binary"
  │     │
  │     ├─> RUN RESEARCH (once):
  │     │     ├─> AskNews search (hot + historical articles)
  │     │     ├─> OR Exa Smart Searcher
  │     │     ├─> OR Perplexity online search
  │     │     └─> Returns formatted research report
  │     │
  │     ├─> BUILD PROMPT:
  │     │     ├─> Title
  │     │     ├─> Background
  │     │     ├─> Resolution criteria
  │     │     ├─> Research report
  │     │     └─> Chain-of-thought instructions
  │     │
  │     ├─> RUN N PREDICTIONS (5x in parallel):
  │     │     │
  │     │     FOR i = 1 to 5:
  │     │       ├─> Call LLM with prompt (temperature=0.3)
  │     │       ├─> LLM generates rationale + "Probability: XX%"
  │     │       ├─> Extract probability via regex
  │     │       ├─> Clamp to 1-99%
  │     │       └─> Store (probability, rationale)
  │     │
  │     ├─> AGGREGATE:
  │     │     ├─> Take median of 5 probabilities
  │     │     ├─> Convert to decimal (0.01-0.99)
  │     │     └─> Combine all rationales into comment
  │     │
  │     └─> SUBMIT TO METACULUS:
  │           ├─> POST forecast: {"probability_yes": 0.XX}
  │           └─> POST comment: "Median: 0.XX\n\n## Rationale 1\n..."
  │
  └─> Print summary & handle errors
END
```

---

## Example Execution

### Question
"Will humans go extinct by 2100?"

### Step-by-Step

1. **Fetch** question details from Metaculus API

2. **Research** (using AskNews):
   ```
   Recent articles about existential risk, AI safety, nuclear weapons...
   ```

3. **Prompt** LLM 5 times with:
   ```
   You are a professional forecaster...
   Question: Will humans go extinct by 2100?
   Resolution: Resolves Yes if no living humans...
   Research: [AskNews articles]
   Before answering write:
   (a) Time left: 75 years
   (b) Status quo: No extinction (humans still alive)
   (c) No scenario: Continued technological progress with safeguards
   (d) Yes scenario: AI catastrophe, nuclear war, or pandemic
   Final answer: "Probability: ZZ%"
   ```

4. **LLM outputs** (5 independent runs):
   ```
   Run 1: "Probability: 2%"
   Run 2: "Probability: 5%"
   Run 3: "Probability: 3%"
   Run 4: "Probability: 4%"
   Run 5: "Probability: 3%"
   ```

5. **Aggregate**: Median([2, 5, 3, 4, 3]) = **3%** = **0.03**

6. **Submit**:
   ```json
   {
     "question": 578,
     "probability_yes": 0.03,
     "probability_yes_per_category": null,
     "continuous_cdf": null
   }
   ```

7. **Post comment** with all 5 rationales

---

## Key Design Decisions

| Decision | Rationale | Line Refs |
|----------|-----------|-----------|
| **Research once, predict 5x** | Separates information gathering from reasoning variance | 449, 472-474 |
| **Median aggregation** | Robust to outlier predictions | 480 |
| **Regex extraction** | Simple parsing (vs. LLM parser in main.py) | 425-435 |
| **Semaphore rate limiting** | Prevents API rate limit errors | 230-231, 244 |
| **Parallel execution** | Speeds up multiple predictions | 472-474, 1061-1071 |
| **Status quo bias prompt** | Improves calibration | 199, 419 |
| **Clamp to 1-99%** | Avoids overconfident 0% or 100% | 432 |

---

## Performance Characteristics

For a **single binary question** with `NUM_RUNS_PER_QUESTION=5`:

- **1 research call** (AskNews/Exa/Perplexity)
- **5 parallel LLM calls** (GPT-4o)
- **Median aggregation** (fast)
- **2 API posts** (prediction + comment)

**Total time**: ~30-60 seconds (depending on LLM latency)
**Total cost**: ~$0.05-0.15 (depending on model and research provider)

---

## Configuration Constants

From lines 43-72 in `main_with_no_framework.py`:

```python
# Execution settings
SUBMIT_PREDICTION = True  # Set to False for testing
USE_EXAMPLE_QUESTIONS = False  # Set to True to use example questions
NUM_RUNS_PER_QUESTION = 5  # Number of predictions to aggregate
SKIP_PREVIOUSLY_FORECASTED_QUESTIONS = True

# API credentials (set in .env file)
METACULUS_TOKEN = os.getenv("METACULUS_TOKEN")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
ASKNEWS_CLIENT_ID = os.getenv("ASKNEWS_CLIENT_ID")
ASKNEWS_SECRET = os.getenv("ASKNEWS_SECRET")
EXA_API_KEY = os.getenv("EXA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Rate limiting
CONCURRENT_REQUESTS_LIMIT = 5  # Line 230
```

---

## Research Provider Selection

The research strategy is selected based on available API keys (lines 257-270):

1. **AskNews** (if `ASKNEWS_CLIENT_ID` and `ASKNEWS_SECRET` set)
   - Fetches hot articles (latest 48 hours)
   - Fetches historical articles (past 60 days)
   - Returns formatted article summaries

2. **Exa Smart Searcher** (if `EXA_API_KEY` set)
   - Runs 2 searches with 10 sites per search
   - Uses advanced filtering
   - Returns prioritized highlights

3. **Perplexity** (if `PERPLEXITY_API_KEY` set)
   - Uses `llama-3.1-sonar-huge-128k-online` model
   - Returns AI-generated research summary

4. **No research** (if no API keys available)
   - Returns empty string

---

## API Endpoints Used

### Metaculus API

1. **Get tournament questions**: `GET /api/posts/`
   - Parameters: `tournament`, `statuses`, `forecast_type`, etc.
   - Returns: List of posts with question details

2. **Get question details**: `GET /api/posts/{post_id}/`
   - Returns: Full question metadata

3. **Submit prediction**: `POST /api/questions/forecast/`
   - Payload: `[{"question": id, "probability_yes": 0.XX}]`
   - Requires: Metaculus token authentication

4. **Post comment**: `POST /api/comments/create/`
   - Payload: `{"text": comment, "on_post": post_id, ...}`
   - Requires: Metaculus token authentication

---

## Error Handling

- All questions run with `return_exceptions=True` (line 1071)
- Exceptions are caught and printed separately (lines 1074-1090)
- Script raises `RuntimeError` at the end if any errors occurred
- Individual question errors don't block other questions

---

## Comparison with Framework Version (main.py)

| Feature | main_with_no_framework.py | main.py |
|---------|--------------------------|---------|
| **Output parsing** | Regex extraction | LLM-based `structure_output()` |
| **API calls** | Direct HTTP requests | `MetaculusApi` abstraction |
| **Code length** | ~1110 lines | ~460 lines |
| **Flexibility** | Full control, transparent | Higher-level, less boilerplate |
| **Dependencies** | Fewer dependencies | Requires `forecasting-tools` |
| **Learning curve** | Better for understanding internals | Better for rapid development |

---

## Summary

The binary question workflow follows a **research → prompt → predict (5x) → aggregate → submit** pattern that balances:

- **Information gathering** (research once to save API costs)
- **Prediction diversity** (5 independent runs with temperature sampling)
- **Robust aggregation** (median to handle outliers)
- **Efficient execution** (parallel async operations throughout)

This architecture is production-tested by Metaculus and achieves good calibration on the AI Forecasting Tournament benchmark.
