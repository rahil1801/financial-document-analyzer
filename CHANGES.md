# CHANGES

## Fixed Deterministic Bugs
- Fixed invalid install guidance by standardizing on `requirements.txt`.
- Replaced undefined `llm = llm` crash with safe LLM initialization.
- Fixed agent tool registration (`tools=[...]` instead of invalid `tool=[...]`).
- Rebuilt PDF reading to use `PyMuPDF (fitz)` with proper error handling.
- Simplified and corrected task configuration to a single reliable analysis task.
- Added strict PDF input validation in API endpoints.

## Improved Prompting Quality
- Rewrote unsafe/hallucination-heavy agent goal/backstory into factual, evidence-first instructions.
- Replaced vague/contradictory task prompts with structured, auditable output requirements.

## Bonus Features Delivered
- Implemented queue-worker concurrency model using `asyncio.Queue` and configurable worker pool.
- Added job lifecycle tracking (`queued`, `processing`, `completed`, `failed`).
- Added MongoDB integration (via `MONGODB_URI`) for users and analysis records.
- Added async job retrieval endpoint and sync fallback endpoint.

## Documentation
- Replaced README with comprehensive setup, bug-fix summary, usage guide, and API docs.
