# Project Memory & Architectural Decisions

## Key Architectural Decisions

1. **Docker Environment & Ports:**
   - Host PostgreSQL Port: `5434` (mapped to container port `5432`).
   - Backend Port: `8000`.
   - Docker container names: `metrology_backend`, `metrology_postgres`.

2. **Database Single Source of Truth:**
   - 11 core tables created via Alembic revision `0001_initial_schema.py`.
   - 11 native PostgreSQL ENUM types.
   - All migrations maintain 100% parity with SQLAlchemy models.

3. **Perception vs Legal Reasoning Boundary:**
   - The OCR perception layer (`app.services.ocr`) extracts candidate declarations and assigns extraction confidence scores.
   - The Rule Engine (`app.services.rule_engine`) executes deterministic statutory rules against declarations.
   - No LLMs, probabilistic models, or OCR confidence thresholds make legal compliance verdicts.

4. **Human-in-the-Loop Preservation:**
   - Declarations contain `is_human_verified: bool`.
   - Manual inspector overrides take precedence over automated OCR extractions.
   - OCR runs record raw text and tokens into `ocr_results` and raw extractions into `declarations.raw_extractions` without overwriting verified values.

5. **Deterministic Legal Rule Aggregation:**
   - Any Check `FAIL` $\implies$ Overall `NON_COMPLIANT` (`status = COMPLETED`).
   - Any Check `REVIEW` (and no `FAIL`) $\implies$ Overall `NEEDS_REVIEW` (`status = REVIEW_REQUIRED`).
   - All Checks `PASS` $\implies$ Overall `COMPLIANT` (`status = COMPLETED`).

