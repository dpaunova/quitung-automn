# quitung_automn

Bulgarian receipt scanning PWA — automated OCR extraction with agentische validation.

`backend/` (Python 3.12, FastAPI) carries the API (auth, receipts, reports, business endpoints), the extraction pipeline (PaddleOCR-VL 1.5 via `extraction/vlm_extractor.py`, mock extractor for dev), agentische validation (`extraction/validator.py` — 6 rules, confidence scoring, threshold 0.85), Excel/PDF report generation (`reports/`), and email dispatch. `frontend/` is a vanilla JS PWA (SPA with hash router, 8 pages). Docker Compose runs 5 services: PostgreSQL, Redis, Backend, Worker (ARQ), Nginx. Local dev uses SQLite, no Redis, mock extractor, frontend served directly from FastAPI.

## Tech stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL (prod) / SQLite (dev) |
| OCR | PaddleOCR-VL 1.5 (mock in dev) |
| Queue | ARQ + Redis (prod only) |
| Frontend | Vanilla JS PWA, hash router |
| Auth | JWT + bcrypt |
| Reports | openpyxl (Excel), reportlab (PDF) |
| Email | aiosmtplib |
| Containers | Docker Compose |

## Quick start (local dev)

```sh
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

App runs at `http://localhost:8000`. Mock extractor returns realistic Bulgarian receipt data without GPU.

## Docker (production)

```sh
cp .env.example .env
docker compose up --build
```

## Verify

```sh
cd backend
pytest                          # all tests
pytest --cov=app --cov-report=term   # with coverage
python -m py_compile app/main.py     # syntax check
```

A change is not done until tests pass locally.

## Structure

```
quitung_automn/
├── backend/
│   ├── app/
│   │   ├── auth/          # JWT auth, bcrypt
│   │   ├── business/      # Business management
│   │   ├── extraction/    # VLM extraction + validation
│   │   ├── receipts/      # Receipt CRUD
│   │   ├── reports/       # Excel/PDF generation, email
│   │   ├── config.py      # Pydantic Settings
│   │   ├── database.py    # SQLAlchemy engine
│   │   ├── models.py      # ORM models
│   │   └── main.py        # FastAPI app + frontend serving
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── css/style.css
│   ├── js/
│   │   ├── api.js         # API client
│   │   ├── app.js         # Init
│   │   ├── router.js      # SPA hash router
│   │   └── pages/         # 8 pages
│   ├── index.html
│   ├── manifest.json, sw.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── tests/
```

## Workflow

1. Non-trivial feature: `/brainstorm` → `/plan` (produces plan in `docs/plans/draft/`) → wait for approval.
2. Move plan to `active/`, implement, tests green at each step.
3. `/review` before pushing or opening a PR.
4. Run the app and verify the feature works in the browser.
5. Move plan to `done/`, fill `## Retro`.

## Rules

Keep it simple:
- Tests must pass before declaring done.
- No secrets in code (use .env).
- All UI text in Bulgarian.
- Validate at system boundaries (user input, file uploads).
- No code comments unless the WHY is non-obvious.
