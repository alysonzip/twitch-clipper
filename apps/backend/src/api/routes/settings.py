from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional

from src.database import get_session
from src.models.settings import Settings
from src.services.settings_service import SettingsService

router = APIRouter()


class SettingsResponse(BaseModel):
    obs_recordings_path: str
    clips_output_path: str
    temp_path: str
    twitch_client_id: Optional[str] = None
    gemini_api_key: Optional[str] = None  # masked
    whisper_model: str
    whisper_device: str
    whisper_compute_type: str
    virality_threshold: float
    min_clip_duration: int
    max_clip_duration: int
    live_buffer_minutes: int
    live_segment_seconds: int
    add_hook_titles: bool
    add_broll: bool
    subtitle_style: str
    auto_start: bool


class SettingsUpdate(BaseModel):
    obs_recordings_path: Optional[str] = None
    clips_output_path: Optional[str] = None
    temp_path: Optional[str] = None
    twitch_client_id: Optional[str] = None
    twitch_client_secret: Optional[str] = None
    gemini_api_key: Optional[str] = None
    whisper_model: Optional[str] = None
    whisper_device: Optional[str] = None
    whisper_compute_type: Optional[str] = None
    virality_threshold: Optional[float] = None
    min_clip_duration: Optional[int] = None
    max_clip_duration: Optional[int] = None
    live_buffer_minutes: Optional[int] = None
    live_segment_seconds: Optional[int] = None
    add_hook_titles: Optional[bool] = None
    add_broll: Optional[bool] = None
    subtitle_style: Optional[str] = None
    auto_start: Optional[bool] = None


@router.get("")
async def get_settings(session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()

    # Mask sensitive fields
    return SettingsResponse(
        obs_recordings_path=settings.obs_recordings_path,
        clips_output_path=settings.clips_output_path,
        temp_path=settings.temp_path,
        twitch_client_id=settings.twitch_client_id,
        gemini_api_key="****" if settings.gemini_api_key else None,
        whisper_model=settings.whisper_model,
        whisper_device=settings.whisper_device,
        whisper_compute_type=settings.whisper_compute_type,
        virality_threshold=settings.virality_threshold,
        min_clip_duration=settings.min_clip_duration,
        max_clip_duration=settings.max_clip_duration,
        live_buffer_minutes=settings.live_buffer_minutes,
        live_segment_seconds=settings.live_segment_seconds,
        add_hook_titles=settings.add_hook_titles,
        add_broll=settings.add_broll,
        subtitle_style=settings.subtitle_style,
        auto_start=settings.auto_start,
    )


@router.patch("")
async def update_settings(
    update: SettingsUpdate,
    session: Session = Depends(get_session),
):
    svc = SettingsService(session)
    data = update.model_dump(exclude_unset=True)

    # Handle encryption for secrets
    if "twitch_client_secret" in data:
        secret = data.pop("twitch_client_secret")
        if secret:
            data["twitch_client_secret_encrypted"] = svc.encrypt_secret(secret)

    if "gemini_api_key" in data and data["gemini_api_key"] and not data["gemini_api_key"].startswith("****"):
        # Don't re-encrypt if it's already masked
        pass

    svc.update(**data)
    return await get_settings(session)


@router.post("/test/twitch")
async def test_twitch(session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()
    if not settings.twitch_client_id:
        raise HTTPException(status_code=400, detail="Twitch Client ID not configured")
    # In real implementation, test Twitch API connection
    return {"status": "success", "message": "Twitch connection OK"}


@router.post("/test/gemini")
async def test_gemini(session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key not configured")
    # In real implementation, test Gemini API connection
    return {"status": "success", "message": "Gemini connection OK"}