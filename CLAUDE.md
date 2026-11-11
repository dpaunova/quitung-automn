# CLAUDE.md

@AGENTS.md

## Claude-specific notes

- Reviews run via the `/review` skill. Run before pushing or opening a PR.
- Verify with `pytest` in `backend/` before declaring anything done.
- To run the app locally: `cd backend && uvicorn app.main:app --reload --port 8000`
- All UI text is in Bulgarian (Cyrillic). Backend error messages and API responses in English.
- Mock extractor is active when `VLM_ENABLED=False` (default for dev).
- Frontend is served directly from FastAPI in dev (no separate server needed).
