from fastapi import APIRouter, Depends
from sqlmodel import Session
from pydantic import BaseModel

from src.database import get_session
from src.models.settings import Settings
from src.services.settings_service import SettingsService

router = APIRouter()


class LiveStatus(BaseModel):
    running: bool
    paused: bool
    current_file: str | None = None
    last_clip: str | None = None


@router.get("/status", response_model=LiveStatus)
async def get_live_status(session: Session = Depends(get_session)):
    # In real implementation, get status from file watcher service
    return LiveStatus(running=False, paused=False, current_file=None, last_clip=None)


@router.post("/pause")
async def pause_live(session: Session = Depends(get_session)):
    # In real implementation, pause file watcher
    return {"message": "Live monitoring paused"}


@router.post("/resume")
async def resume_live(session: Session = Depends(get_session)):
    # In real implementation, resume file watcher
    return {"message": "Live monitoring resumed"}


@router.post("/start")
async def start_live(session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()

    # Validate paths exist
    from pathlib import Path
    if not Path(settings.obs_recordings_path).exists():
        return {"error": f"OBS recordings path does not exist: {settings.obs_recordings_path}"}

    # In real implementation, start file watcher
    return {"message": "Live monitoring started"}


@router.post("/stop")
async def stop_live(session: Session = Depends(get_session)):
    # In real implementation, stop file watcher
    return {"message": "Live monitoring stopped"}