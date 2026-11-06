from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from pydantic import BaseModel
from typing import Optional

from src.database import get_session
from src.models.settings import Settings
from src.services.settings_service import SettingsService

router = APIRouter()


class AuthUrlResponse(BaseModel):
    auth_url: str


class VOD(BaseModel):
    id: str
    title: str
    url: str
    created_at: str
    duration: str
    view_count: int


@router.get("/auth-url", response_model=AuthUrlResponse)
async def get_auth_url(session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()

    if not settings.twitch_client_id:
        raise HTTPException(status_code=400, detail="Twitch Client ID not configured")

    redirect_uri = "http://localhost:8765/api/v1/twitch/callback"
    scopes = "user:read:email clips:read"
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={settings.twitch_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
    )
    return {"auth_url": auth_url}


@router.get("/callback")
async def twitch_callback(code: str = Query(...), session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()

    if not settings.twitch_client_id or not settings.twitch_client_secret_encrypted:
        raise HTTPException(status_code=400, detail="Twitch credentials not configured")

    # In real implementation, exchange code for access token
    # This would call Twitch API to get access_token and refresh_token
    # Then store them encrypted in settings

    return {"message": "Twitch connected successfully! You can close this window."}


@router.get("/vods", response_model=list[VOD])
async def list_vods(session: Session = Depends(get_session)):
    svc = SettingsService(session)
    settings = svc.get()

    if not settings.twitch_access_token:
        raise HTTPException(status_code=401, detail="Not authenticated with Twitch")

    # In real implementation, call Twitch Helix API to get user's VODs
    # Return mock data for now
    return []


@router.get("/vods/{vod_id}")
async def get_vod(vod_id: str, session: Session = Depends(get_session)):
    # In real implementation, call Twitch Helix API to get VOD details
    return {"id": vod_id, "title": "Sample VOD", "url": f"https://twitch.tv/videos/{vod_id}"}