import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.business.routes import router as business_router
from app.config import settings
from app.database import create_all
from app.receipts.routes import router as receipts_router
from app.reports.routes import router as reports_router

app = FastAPI(
    title="Quitung Automn API",
    description="Backend for the Bulgarian receipt scanning PWA",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS (allow all origins for development)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(receipts_router)
app.include_router(reports_router)
app.include_router(business_router)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    create_all()

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Static files (uploaded receipts / reports)
# ---------------------------------------------------------------------------
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.get("/api")
def api_root():
    return {"status": "ok", "service": "Quitung Automn API"}


app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/manifest.json")
def manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(FRONTEND_DIR / "sw.js", media_type="application/javascript")


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    file_path = FRONTEND_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(FRONTEND_DIR / "index.html")
