"""FastAPI application for GST Filing Portal."""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import init_db
from .config import settings
from .routes import gstins, upload, processing, results, audit, companies

app = FastAPI(
    title="GST Filing Portal",
    description="Web portal for GST return automation",
    version="1.0.0",
)

# CORS for frontend (dev mode + ngrok)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gstins.router)
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(results.router)
app.include_router(audit.router)
app.include_router(companies.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "project_root": str(settings.project_root)}


# Serve frontend build (production / ngrok sharing)
FRONTEND_DIST = settings.project_root / "portal" / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static")

    @app.get("/")
    async def serve_root():
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve frontend SPA — all non-API routes return index.html."""
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
