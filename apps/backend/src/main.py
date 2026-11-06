from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db
from src.api.routes import clips, jobs, settings, twitch, live


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Twitch Clipper API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for Electron (app:// protocol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["app://.", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "twitch-clipper-backend"}

# Routes
app.include_router(clips.router, prefix="/api/v1/clips", tags=["clips"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(twitch.router, prefix="/api/v1/twitch", tags=["twitch"])
app.include_router(live.router, prefix="/api/v1/live", tags=["live"])


if __name__ == "__main__":
    import sys
    import uvicorn
    if getattr(sys, "frozen", False):
        # Executavel empacotado (PyInstaller): nao usa import string nem reload
        uvicorn.run(app, host="0.0.0.0", port=8765)
    else:
        uvicorn.run("src.main:app", host="0.0.0.0", port=8765, reload=True)