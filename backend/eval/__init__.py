"""
Standalone RAGAS evaluation tooling.

This package is deliberately kept OUTSIDE `app/` and is never imported by the
running FastAPI application. It exists to answer one question offline: "how
good are the answers coming out of /api/query, measured against a hand-written
golden set?" — see `run_ragas_eval.py` for the actual script and `golden_set.json`
for the test questions.

Run it with (from the backend/ directory, venv active, API running locally):
    python -m eval.run_ragas_eval
"""
