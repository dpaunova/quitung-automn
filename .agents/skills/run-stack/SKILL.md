---
name: run-stack
description: "Start the app and verify a change works in the real app. Use after any change to frontend or backend code, or when the user says 'run the app', 'test it for real', 'start the server'."
---

# Run the stack

## Local dev (no Docker)

```sh
cd backend
uvicorn app.main:app --reload --port 8000
```

App serves both API and frontend at `http://localhost:8000`.

- Mock extractor active when `VLM_ENABLED=False` (default)
- SQLite database at `backend/quitung.db`
- Uploads stored in `backend/uploads/`

## Docker (production-like)

```sh
cp .env.example .env
docker compose up --build
```

5 services: PostgreSQL, Redis, Backend, Worker (ARQ), Nginx.

## Verification checklist

After starting the app:

1. Open `http://localhost:8000` in browser
2. Register a new account or login
3. Test the feature you changed
4. Check browser console for errors
5. Check network tab for failed requests

## Data reset

Delete `backend/quitung.db` to start fresh (local dev).
For Docker: `docker compose down -v` removes volumes.
