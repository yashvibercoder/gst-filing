"""FastAPI application for GST Filing Portal."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .config import settings
from .routes import gstins, upload, processing, results

app = FastAPI(
    title="GST Filing Portal",
    description="Web portal for GST return automation",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gstins.router)
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(results.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "project_root": str(settings.project_root)}
